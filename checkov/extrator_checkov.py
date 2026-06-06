import os
import json
import csv

# 1. Definição dos caminhos e regras
diretorio_checkov = './out'
arquivo_saida = '../analises/matriz_resultados_checkov.csv'

regras_finops = [
    'CKV_FINOPS_01', 
    'CKV_FINOPS_02', 
    'CKV_FINOPS_03', 
    'CKV_FINOPS_04A', 
    'CKV_FINOPS_04B'
]

dados_matriz = []

# 2. Iterar sobre todos os arquivos JSON na pasta do Checkov
for arquivo in sorted(os.listdir(diretorio_checkov)):
    if arquivo.endswith('.json'):
        caminho_arquivo = os.path.join(diretorio_checkov, arquivo)
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            try:
                conteudo = json.load(f)
            except json.JSONDecodeError:
                print(f"Erro ao ler o arquivo {arquivo}. Pulando...")
                continue
        
        # O Checkov pode retornar uma lista (se houver múltiplos frameworks) ou um dict
        if isinstance(conteudo, dict):
            conteudo = [conteudo]
            
        # Inicializa o dicionário de resultados para este plano
        id_caso = arquivo.replace('.json', '')
        resultados_plano = {'ID do Caso': id_caso}
        
        # Inicia todas as regras como N/A (Não Avaliado)
        for regra in regras_finops:
            resultados_plano[regra] = "N/A"
            
        falhou_geral = False
        
        # 3. Analisar os resultados dentro do JSON
        for framework_result in conteudo:
            resultados = framework_result.get('results', {})
            
            # Checar falhas (Se falhou em 1 recurso, a regra toda falha para o plano)
            for falha in resultados.get('failed_checks', []):
                check_id = falha.get('check_id')
                if check_id in regras_finops:
                    resultados_plano[check_id] = "FAILED"
                    falhou_geral = True
                    
            # Checar acertos (Só marca PASSED se não houver falha prévia registrada)
            for acerto in resultados.get('passed_checks', []):
                check_id = acerto.get('check_id')
                if check_id in regras_finops and resultados_plano[check_id] != "FAILED":
                    resultados_plano[check_id] = "PASSED"

        # 4. Veredito Final do Plano segundo o Checkov
        resultados_plano['Veredito Checkov'] = "FAILED" if falhou_geral else "PASSED"
        
        dados_matriz.append(resultados_plano)

# 5. Exportar os resultados para um arquivo CSV
colunas = ['ID do Caso'] + regras_finops + ['Veredito Checkov']

with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_csv:
    escritor = csv.DictWriter(f_csv, fieldnames=colunas, delimiter=';')
    escritor.writeheader()
    escritor.writerows(dados_matriz)

print(f"Extração concluída com sucesso! Matriz salva em: {arquivo_saida}")