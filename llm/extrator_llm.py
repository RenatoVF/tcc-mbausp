import os
import json
import csv

# 1. Definição dos caminhos e regras
diretorio_llm = './out'
arquivo_saida = '../analises/matriz_resultados_llm.csv'

regras_finops = [
    'CKV_FINOPS_01', 
    'CKV_FINOPS_02', 
    'CKV_FINOPS_03', 
    'CKV_FINOPS_04A', 
    'CKV_FINOPS_04B'
]

dados_matriz = []

# 2. Iterar sobre todos os arquivos JSON na pasta de saída do LLM
for arquivo in sorted(os.listdir(diretorio_llm)):
    if arquivo.endswith('.json'):
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