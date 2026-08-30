import os
import json
import time
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

# 3. Função de Engenharia de Dados para Limpar o JSON (Em memória)
def otimizar_plano_terraform(plano_json_str):
    """
    Filtra o JSON massivo do Terraform, extraindo apenas variáveis globais, 
    provedores e os atributos essenciais dos recursos.
    """
    try:
        dados = json.loads(plano_json_str)
        
        # Extração dos valores reais das variáveis (.tfvars)
        variaveis_limpas = {}
        for var_nome, var_info in dados.get("variables", {}).items():
            variaveis_limpas[var_nome] = var_info.get("value")
            
        payload_otimizado = {
            "variaveis_globais": variaveis_limpas,
            "provedores": dados.get("configuration", {}).get("provider_config", {}),
            "recursos_modificados": []
        }
        
        # Filtra apenas os recursos modificados/criados
        for res in dados.get("resource_changes", []):
            acoes = res.get("change", {}).get("actions", [])
            if acoes == ["delete"] or acoes == ["no-op"]:
                continue 
                
            after = res.get("change", {}).get("after", {})
            if isinstance(after, dict):
                payload_otimizado["recursos_modificados"].append({
                    "tipo": res.get("type"),
                    "nome": res.get("name"),
                    "tags": after.get("tags"),
                    "instance_type": after.get("instance_type"),
                    "instance_class": after.get("instance_class")
                })
                
        return json.dumps(payload_otimizado, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Aviso: Não foi possível otimizar o JSON. Erro: {e}")
        return json.dumps({"erro": str(e)})

# 4. O Prompt de Engenharia (Role Prompting e Zero-Shot)
prompt_sistema = """Você é um Engenheiro Sênior de Nuvem e Auditor de FinOps.
Sua tarefa é analisar o plano de execução do Terraform (fornecido em formato JSON otimizado) e validar se a infraestrutura está em estrita conformidade com as seguintes políticas de FinOps:

- CKV_FINOPS_01: Os recursos principais (estritamente os tipos 'aws_instance', 'aws_db_instance' e 'aws_s3_bucket') devem conter as seguintes três tags obrigatórias, não podendo estar vazias: 'Projeto', 'Time Responsável' e 'Ambiente'. Ignore completamente a ausência de tags em outros tipos de recursos.
- CKV_FINOPS_02: A tag 'Ambiente' só pode receber de forma estrita um dos dois valores: 'PRD' ou 'HML'.
- CKV_FINOPS_03: Todo recurso deve ser provisionado exclusivamente na região 'us-east-1' (Verifique o bloco 'provedores'. Se a região for uma referência de variável como 'var.aws_region', consulte o bloco 'variaveis_globais' para descobrir o valor real que será provisionado).
- CKV_FINOPS_04A: Se o valor da tag 'Ambiente' for 'HML', instâncias computacionais EC2 (aws_instance) devem pertencer obrigatoriamente à família 't' (ex: t2.micro, t3.medium).
- CKV_FINOPS_04B: Se o valor da tag 'Ambiente' for 'HML', instâncias de banco de dados RDS (aws_db_instance) devem pertencer obrigatoriamente à família 't' (ex: db.t3.micro).

Analise os recursos declarados e retorne a avaliação ESTRITAMENTE em formato JSON. O JSON de resposta deve conter exatamente as chaves 'CKV_FINOPS_01', 'CKV_FINOPS_02', 'CKV_FINOPS_03', 'CKV_FINOPS_04A' e 'CKV_FINOPS_04B'.
O valor de cada chave deve ser 'PASSED' se o plano cumpre integralmente a regra, ou 'FAILED' se o plano violar a regra em qualquer recurso aplicável. 
Adicione uma chave 'justificativa' contendo um breve resumo dos motivos das aprovações ou falhas encontradas."""

# 5. Iteração sobre o Dataset (os 30 planos JSON originais)
for arquivo in sorted(os.listdir(pasta_planos)):
    if arquivo.endswith(".json"):
        caminho_arquivo = os.path.join(pasta_planos, arquivo)
        
        # Lê o conteúdo bruto do arquivo
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            plano_json_bruto = f.read()
            
        print(f"Otimizando e enviando para o LLM: {arquivo}...")
        
        # Aplica a otimização em memória para economizar tokens
        plano_otimizado = otimizar_plano_terraform(plano_json_bruto)
        
        try:
            # Chamada à API parametrizada
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0, 
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Analise o seguinte plano do Terraform:\n\n{plano_otimizado}"}
                ]
            )
            
            # Formatação da saída e injeção da rastreabilidade
            resultado_dict = json.loads(response.choices[0].message.content)
            resultado_dict["arquivo_analisado"] = arquivo
            
            # Salvando a avaliação final do LLM
            caminho_saida = os.path.join(pasta_saida, f"llm_eval_{arquivo}")
            with open(caminho_saida, "w", encoding="utf-8") as out_f:
                json.dump(resultado_dict, out_f, indent=4, ensure_ascii=False)
                
            print(f"[OK] Veredito do {arquivo} salvo com sucesso.")
            
            # Pausa de segurança de 2 segundos para respeitar o limite (Rate Limit) da API
            time.sleep(2)
            
        except Exception as e:
            print(f"[ERRO] Falha ao processar {arquivo}: {e}")

print("\n--- Auditoria automatizada pelo LLM concluída com sucesso! Verifique a pasta 'out'. ---")