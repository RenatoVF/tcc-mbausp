import os
import json
import time
import datetime
import hashlib
import openai
from openai import OpenAI

# 1. Lê a chave da API injetada pelo Docker via .env
chave_api = os.environ.get("OPENAI_API_KEY")
if not chave_api:
    raise ValueError("Chave da OpenAI não encontrada. Verifique seu arquivo .env!")

client = OpenAI(api_key=chave_api)

# 2. Definição dos diretórios
pasta_planos = "./sadcloud/tfvars"
pasta_saida = "./out"

# Cria a pasta de saída (no volume mapeado) se ela não existir
os.makedirs(pasta_saida, exist_ok=True)

# Nome do modelo solicitado à API. É um "alias" da OpenAI (não uma versão
# fixa/"snapshot"): a OpenAI pode apontá-lo para uma versão de modelo
# diferente ao longo do tempo sem aviso. Por isso registramos, para cada
# chamada, o valor de 'response.model' devolvido pela API (ver mais abaixo),
# que é a versão EXATA que de fato respondeu - essa é a informação
# confiável para reprodutibilidade, não o nome pedido aqui.
MODELO_SOLICITADO = "gpt-4o"
TEMPERATURA = 0

# Retomabilidade (ajuste feito apos duvida sobre credito disponivel na API):
# se a pasta de saida ja tiver resultados de uma execucao anterior (ex.:
# interrompida por falta de credito), preserva o conjunto de modelos
# resolvidos e o timestamp de inicio originais, para que os metadados finais
# reflitam o historico completo mesmo quando a execucao e retomada em partes.
caminho_metadata = os.path.join(pasta_saida, "metadata_execucao.json")
modelos_resolvidos = set()
timestamp_inicio = datetime.datetime.now(datetime.timezone.utc).isoformat()
if os.path.exists(caminho_metadata):
    try:
        with open(caminho_metadata, "r", encoding="utf-8") as meta_f:
            metadata_anterior = json.load(meta_f)
        modelos_resolvidos.update(metadata_anterior.get("modelos_resolvidos", []))
        if metadata_anterior.get("timestamp_inicio_utc"):
            timestamp_inicio = metadata_anterior["timestamp_inicio_utc"]
    except Exception as e:
        print(f"Aviso: nao foi possivel ler metadata_execucao.json anterior ({e}). Prosseguindo com metadados novos.")

# 3. Função de Engenharia de Dados para Limpar o JSON (Em memória)
#
# NOTA (ajuste feito após conversa com o orientador): esta função já enviou, em versões
# anteriores, um bloco 'variaveis_globais' com os valores resolvidos das
# variáveis do plano, para que o LLM cruzasse manualmente referências como
# 'var.aws_region' com o valor real vindo do .tfvars — enquanto o Checkov lê a
# região já resolvida diretamente do atributo 'region' de cada recurso (um
# campo computado pelo próprio Terraform, igual para valor literal ou vindo de
# variável). Um estudo de ablação (ver ablacao_preprocessamento.md) mostrou que
# essa diferença era decisiva: sem o bloco de variáveis, a acurácia do LLM em
# CKV_FINOPS_03 caía de 1,000 para 0,077. Por isso a função agora extrai o
# atributo 'region' diretamente de cada recurso, do mesmo jeito que o Checkov
# lê, eliminando a necessidade do bloco de variáveis e do cruzamento manual —
# os dois avaliadores passam a consumir exatamente o mesmo dado resolvido.
def otimizar_plano_terraform(plano_json_str):
    """
    Filtra o JSON massivo do Terraform, extraindo apenas os atributos
    essenciais (já resolvidos) de cada recurso modificado/criado.
    """
    try:
        dados = json.loads(plano_json_str)

        payload_otimizado = {
            "recursos_modificados": []
        }
        
        # Filtra apenas os recursos modificados/criados
        for res in dados.get("resource_changes", []):
            acoes = res.get("change", {}).get("actions", [])
            if acoes == ["delete"] or acoes == ["no-op"]:
                continue 
                
            after = res.get("change", {}).get("after", {})
            if isinstance(after, dict):
                # Minimizacao de dados (ajuste feito apos conversa com o orientador):
                # so repassamos as 3 tags que alguma das 5 regras de FinOps
                # de fato usa (Projeto, Time Responsavel, Ambiente) - outras
                # tags eventualmente presentes no recurso (ex.: 'Name') nao
                # sao relevantes para nenhuma regra e nao sao enviadas a API.
                tags_brutas = after.get("tags") or {}
                tags_relevantes = {
                    chave: tags_brutas.get(chave)
                    for chave in ("Projeto", "Time Responsável", "Ambiente")
                    if chave in tags_brutas
                }
                payload_otimizado["recursos_modificados"].append({
                    "tipo": res.get("type"),
                    "nome": res.get("name"),
                    "tags": tags_relevantes,
                    "instance_type": after.get("instance_type"),
                    "instance_class": after.get("instance_class"),
                    "region": after.get("region")
                })
                
        return json.dumps(payload_otimizado, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Aviso: Não foi possível otimizar o JSON. Erro: {e}")
        return json.dumps({"erro": str(e)})

# 4. O Prompt de Engenharia (Role Prompting e Zero-Shot)
prompt_sistema = """Você é um Engenheiro Sênior de Nuvem e Auditor de FinOps.
Sua tarefa é analisar o plano de execução do Terraform (fornecido em formato JSON otimizado) e validar se a infraestrutura está em estrita conformidade com as seguintes políticas de FinOps:

- CKV_FINOPS_01: Para decidir o valor desta chave, siga este procedimento NA ORDEM EXATA e considere SOMENTE os recursos dos tipos 'aws_instance', 'aws_db_instance' e 'aws_s3_bucket' (ignore completamente outros tipos de recursos): (1) Se NENHUM recurso desses três tipos existir no plano, responda 'N/A' e pare. (2) Para cada um desses recursos, verifique SOMENTE se as tags 'Projeto', 'Time Responsável' e 'Ambiente' existem e não estão vazias (chave ausente ou string vazia conta como violação; qualquer outro valor não-vazio conta como presente). NÃO julgue aqui se o VALOR da tag 'Ambiente' é válido ('PRD' ou 'HML') — isso é avaliado exclusivamente pela regra CKV_FINOPS_02, nunca por esta. Uma tag 'Ambiente' com um valor como 'DEV' ou 'STG' CONTA como presente e preenchida para efeitos desta regra, mesmo sendo um valor inválido para CKV_FINOPS_02. (3) Se alguma das três tags obrigatórias estiver ausente ou vazia em pelo menos um desses recursos, responda 'FAILED'. (4) Caso contrário, responda 'PASSED'.
- CKV_FINOPS_02: Para decidir o valor desta chave, siga este procedimento NA ORDEM EXATA, considerando os mesmos recursos de CKV_FINOPS_01 ('aws_instance', 'aws_db_instance', 'aws_s3_bucket'): (1) Se NENHUM desses recursos existir no plano, responda 'N/A' e pare. (2) Para cada um desses recursos que tenha a tag 'Ambiente' preenchida, verifique se o valor é EXATAMENTE 'PRD' ou 'HML'. (3) Se algum desses recursos tiver a tag 'Ambiente' com um valor diferente de 'PRD' e de 'HML' (ex.: 'DEV', 'STG', 'producao'), responda 'FAILED'. Esta violação é EXCLUSIVA de CKV_FINOPS_02 — nunca marque CKV_FINOPS_01 como 'FAILED' por causa de um valor de 'Ambiente' inválido (CKV_FINOPS_01 avalia apenas se a tag existe e não está vazia, não se o valor é válido). (4) Caso contrário, responda 'PASSED'.
- CKV_FINOPS_03: Todo recurso deve ser provisionado exclusivamente na região 'us-east-1'. Verifique o campo 'region' de cada recurso em 'recursos_modificados' (esse valor já vem resolvido pelo Terraform, seja a região definida no código como valor literal ou através de uma variável — você não precisa fazer nenhuma resolução adicional, apenas comparar o valor de 'region' com 'us-east-1'). Esta regra se aplica aos tipos 'aws_instance', 'aws_db_instance', 'aws_s3_bucket', 'aws_elb', 'aws_lb' e 'aws_eks_cluster'; se o plano não contiver nenhum recurso desses tipos, retorne 'N/A'.
- CKV_FINOPS_04A: Para decidir o valor desta chave, siga este procedimento NA ORDEM EXATA: (1) Verifique se existe pelo menos um recurso do tipo 'aws_instance' no plano. Se NÃO existir nenhum, responda 'N/A' e pare — não avalie mais nada para esta regra. (2) Se existir pelo menos um 'aws_instance', verifique se algum deles tem a tag 'Ambiente' igual a 'HML' E 'instance_type' que NÃO comece com a letra 't' (ex.: m5.large, c5.xlarge não passam; t2.micro, t3.medium passam). Se essa condição for verdadeira para pelo menos um recurso, responda 'FAILED'. (3) Em qualquer outro caso — incluindo quando TODOS os 'aws_instance' do plano têm 'Ambiente' diferente de 'HML' — responda 'PASSED'. A ÚNICA razão válida para responder 'N/A' nesta regra é o passo (1) não ter encontrado nenhum 'aws_instance' no plano; nunca responda 'N/A' por causa do valor da tag 'Ambiente'. Uma violação desta regra é EXCLUSIVA de CKV_FINOPS_04A — nunca marque CKV_FINOPS_02 como 'FAILED' por causa dela; um valor de 'Ambiente' igual a 'HML' é válido para CKV_FINOPS_02 e não deve, por si só, causar falha nela.
- CKV_FINOPS_04B: Para decidir o valor desta chave, siga este procedimento NA ORDEM EXATA: (1) Verifique se existe pelo menos um recurso do tipo 'aws_db_instance' no plano. Se NÃO existir nenhum, responda 'N/A' e pare — não avalie mais nada para esta regra. (2) Se existir pelo menos um 'aws_db_instance', verifique se algum deles tem a tag 'Ambiente' igual a 'HML' E 'instance_class' que NÃO comece com 'db.t' (ex.: db.m5.large não passa; db.t3.micro passa). Se essa condição for verdadeira para pelo menos um recurso, responda 'FAILED'. (3) Em qualquer outro caso — incluindo quando TODOS os 'aws_db_instance' do plano têm 'Ambiente' diferente de 'HML' — responda 'PASSED'. A ÚNICA razão válida para responder 'N/A' nesta regra é o passo (1) não ter encontrado nenhum 'aws_db_instance' no plano; nunca responda 'N/A' por causa do valor da tag 'Ambiente'. Uma violação desta regra é EXCLUSIVA de CKV_FINOPS_04B — nunca marque CKV_FINOPS_02 como 'FAILED' por causa dela; um valor de 'Ambiente' igual a 'HML' é válido para CKV_FINOPS_02 e não deve, por si só, causar falha nela.

IMPORTANTE — independência das regras: avalie cada uma das cinco regras acima de forma estritamente isolada, usando apenas o critério exato descrito para ela. Nunca deixe uma violação encontrada em uma regra "vazar" para o veredito de outra regra, mesmo que ambas estejam relacionadas ao mesmo recurso ou à mesma tag. Exemplos do que NÃO fazer: um valor de 'Ambiente' inválido é violação exclusiva de CKV_FINOPS_02, nunca de CKV_FINOPS_01; uma instância de família errada em 'HML' é violação exclusiva de CKV_FINOPS_04A ou CKV_FINOPS_04B, nunca de CKV_FINOPS_02.

Analise os recursos declarados e retorne a avaliação ESTRITAMENTE em formato JSON. O JSON de resposta deve conter exatamente as chaves 'CKV_FINOPS_01', 'CKV_FINOPS_02', 'CKV_FINOPS_03', 'CKV_FINOPS_04A' e 'CKV_FINOPS_04B'.
O valor de cada chave deve ser exatamente um dentre três possíveis: 'PASSED' (o plano cumpre integralmente a regra em todos os recursos aplicáveis), 'FAILED' (o plano viola a regra em pelo menos um recurso aplicável) ou 'N/A' (o plano não contém nenhum recurso ao qual esta regra se aplique, conforme os critérios de aplicabilidade descritos acima para cada regra). Nunca deixe uma chave sem valor e nunca utilize um quarto valor além desses três.
Adicione uma chave 'justificativa' contendo um breve resumo dos motivos das aprovações, falhas ou não aplicabilidades encontradas."""

# 5. Iteração sobre o Dataset (os 30 planos JSON originais)
for arquivo in sorted(os.listdir(pasta_planos)):
    if arquivo.endswith(".json"):
        caminho_arquivo = os.path.join(pasta_planos, arquivo)
        caminho_saida = os.path.join(pasta_saida, f"llm_eval_{arquivo}")

        # Retomabilidade: pula planos que ja tem um veredito salvo de uma
        # execucao anterior, para nao pagar novamente pela chamada a API de
        # planos ja avaliados com sucesso.
        if os.path.exists(caminho_saida):
            print(f"[PULADO] {arquivo} ja tem veredito salvo em {caminho_saida}.")
            continue

        # Lê o conteúdo bruto do arquivo
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            plano_json_bruto = f.read()
            
        print(f"Otimizando e enviando para o LLM: {arquivo}...")
        
        # Aplica a otimização em memória para economizar tokens
        plano_otimizado = otimizar_plano_terraform(plano_json_bruto)
        
        try:
            # Chamada à API parametrizada
            response = client.chat.completions.create(
                model=MODELO_SOLICITADO,
                temperature=TEMPERATURA, 
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Analise o seguinte plano do Terraform:\n\n{plano_otimizado}"}
                ]
            )
            
            # Formatação da saída e injeção da rastreabilidade
            resultado_dict = json.loads(response.choices[0].message.content)
            resultado_dict["arquivo_analisado"] = arquivo
            # Versão EXATA do modelo que respondeu (pode diferir do alias
            # solicitado, ver comentário acima) - registrada por chamada
            # para detectar qualquer troca de versão no meio da execução.
            resultado_dict["_modelo_resolvido"] = response.model
            modelos_resolvidos.add(response.model)
            
            # Salvando a avaliação final do LLM
            with open(caminho_saida, "w", encoding="utf-8") as out_f:
                json.dump(resultado_dict, out_f, indent=4, ensure_ascii=False)
                
            print(f"[OK] Veredito do {arquivo} salvo com sucesso.")
            
            # Pausa de segurança de 2 segundos para respeitar o limite (Rate Limit) da API
            time.sleep(2)
            
        except Exception as e:
            print(f"[ERRO] Falha ao processar {arquivo}: {e}")

# Metadados agregados desta execução (reprodutibilidade):
# versão(ões) de modelo que de fato respondeu, versão do SDK da OpenAI,
# temperatura usada, hash do prompt (para saber exatamente qual versão do
# protocolo gerou esta rodada, ver historico_prompt.md) e janela de tempo
# da execução.
metadados_execucao = {
    "modelo_solicitado": MODELO_SOLICITADO,
    "modelos_resolvidos": sorted(modelos_resolvidos),
    "temperatura": TEMPERATURA,
    "sdk_openai_versao": openai.__version__,
    "prompt_sistema_sha256": hashlib.sha256(prompt_sistema.encode("utf-8")).hexdigest(),
    "timestamp_inicio_utc": timestamp_inicio,
    "timestamp_fim_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
with open(os.path.join(pasta_saida, "metadata_execucao.json"), "w", encoding="utf-8") as meta_f:
    json.dump(metadados_execucao, meta_f, indent=4, ensure_ascii=False)

if len(modelos_resolvidos) > 1:
    print(f"[AVISO] Mais de uma versão de modelo respondeu nesta execução: {sorted(modelos_resolvidos)}")

print("\n--- Auditoria automatizada pelo LLM concluída com sucesso! Verifique a pasta 'out'. ---")