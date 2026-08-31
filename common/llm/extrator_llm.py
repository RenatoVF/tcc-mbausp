import os
import sys
import json
import csv

# 1. Definição dos caminhos e regras
# Uso padrão (sem argumentos): python extrator_llm.py -> lê ./out e grava
# em ../analises/matriz_resultados_llm.csv, como sempre.
# Uso com argumentos (usado no estudo de ablação do pré-processamento):
#   python extrator_llm.py <pasta_de_entrada> <arquivo_csv_de_saida>
diretorio_llm = sys.argv[1] if len(sys.argv) > 1 else './out'
arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else '../analises/matriz_resultados_llm.csv'

# Checagem de integridade: avaliador_llm.py so grava
# 'metadata_execucao.json' quando termina de processar todos os planos. Se
# esse arquivo nao existir, a execucao foi interrompida antes do fim (por
# exemplo, "docker compose up --build -d" seguido do extrator cedo demais,
# antes do container terminar as chamadas a API) e a matriz abaixo
# provavelmente esta incompleta.
if not os.path.exists(os.path.join(diretorio_llm, "metadata_execucao.json")):
    print("=" * 70)
    print(f"[AVISO] metadata_execucao.json nao encontrado em '{diretorio_llm}'.")
    print("Isso normalmente indica que avaliador_llm.py foi interrompido antes")
    print("de terminar (ex.: rodou com 'docker compose up --build -d' e o")
    print("extrator foi chamado antes do container terminar). Confira o numero")
    print("de casos processados abaixo antes de usar esta matriz nas analises.")
    print("=" * 70)

regras_finops = [
    'CKV_FINOPS_01', 
    'CKV_FINOPS_02', 
    'CKV_FINOPS_03', 
    'CKV_FINOPS_04A', 
    'CKV_FINOPS_04B'
]

dados_matriz = []

# 2. Iterar sobre todos os arquivos JSON na pasta de saída do LLM
# ('metadata_execucao.json' tambem termina em .json, mas nao e um caso
# avaliado - e o resumo da execucao gravado pelo avaliador_llm.py - entao
# precisa ser explicitamente ignorado aqui.
for arquivo in sorted(os.listdir(diretorio_llm)):
    if arquivo.endswith('.json') and arquivo != 'metadata_execucao.json':
        caminho_arquivo = os.path.join(diretorio_llm, arquivo)
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            try:
                conteudo = json.load(f)
            except json.JSONDecodeError:
                print(f"Erro ao ler o arquivo {arquivo}. Pulando...")
                continue
        
        # Pega o nome do arquivo original analisado (salvo na chave 'arquivo_analisado') 
        # e remove o .json para manter o padrão de "ID do Caso" igual ao do Checkov
        nome_original = conteudo.get("arquivo_analisado", arquivo)
        id_caso = nome_original.replace('.json', '')
        
        resultados_plano = {'ID do Caso': id_caso}
        
        falhou_geral = False
        
        # 3. Extrai os resultados de cada regra FinOps
        for regra in regras_finops:
            status = conteudo.get(regra, "N/A")
            resultados_plano[regra] = status
            
            # Se a IA apontou falha em qualquer regra, o plano todo falha
            if status == "FAILED":
                falhou_geral = True
        
        # 4. Veredito Final do Plano segundo o LLM
        resultados_plano['Veredito LLM'] = "FAILED" if falhou_geral else "PASSED"
        
        dados_matriz.append(resultados_plano)

# 5. Exportar os resultados para um arquivo CSV
colunas = ['ID do Caso'] + regras_finops + ['Veredito LLM']

with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_csv:
    escritor = csv.DictWriter(f_csv, fieldnames=colunas, delimiter=';')
    escritor.writeheader()
    escritor.writerows(dados_matriz)

print(f"Extração concluída com sucesso! Matriz salva em: {arquivo_saida}")