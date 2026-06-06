import os
import json
import csv

# 1. Definição dos caminhos
diretorio_infracost = './out'
arquivo_saida = '../analises/matriz_custos_infracost.csv'

dados_custos = []

# 2. Iterar sobre todos os arquivos JSON na pasta de saída do Infracost
if not os.path.exists(diretorio_infracost):
    print(f"[ERRO] A pasta {diretorio_infracost} não foi encontrada.")
else:
    for arquivo in sorted(os.listdir(diretorio_infracost)):
        if arquivo.endswith('.infracost.json'):
            caminho_arquivo = os.path.join(diretorio_infracost, arquivo)
            
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                try:
                    conteudo = json.load(f)
                except json.JSONDecodeError:
                    print(f"Erro ao ler o arquivo {arquivo}. Pulando...")
                    continue
            
            # Pega o nome do arquivo e remove o sufixo '.infracost.json' para ser o ID do Caso
            id_caso = arquivo.replace('.infracost.json', '')
            
            # Extrai o custo mensal total. O Infracost guarda esse valor em 'totalMonthlyCost'
            custo_mensal = conteudo.get('totalMonthlyCost', 0.0)
            
            # Converte para string e troca o ponto por vírgula para manter compatibilidade com o Excel PT-BR
            custo_mensal_ptbr = str(custo_mensal).replace('.', ',')
            
            dados_custos.append({
                'ID do Caso': id_caso,
                'Custo Mensal Total ($)': custo_mensal_ptbr
            })

    # 3. Exportar os resultados para um arquivo CSV
    colunas = ['ID do Caso', 'Custo Mensal Total ($)']

    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_csv:
        # Usando ponto e vírgula como delimitador para facilitar a abertura no Excel
        escritor = csv.DictWriter(f_csv, fieldnames=colunas, delimiter=';')
        escritor.writeheader()
        escritor.writerows(dados_custos)

    print(f"\n--- Extração de custos concluída com sucesso! ---")
    print(f"Os dados foram salvos em: {arquivo_saida}")