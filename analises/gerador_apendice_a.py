import csv
import os

# 1. Definição dos caminhos dos arquivos
arquivo_amostras = 'amostras.md'
arquivo_custos = 'matriz_custos_infracost.csv'
arquivo_saida = 'apendice_a_matriz_amostra.csv'

# Dicionário para armazenar os custos por Arquivo Base
custos = {}

# 2. Ler o arquivo de custos do Infracost
if os.path.exists(arquivo_custos):
    with open(arquivo_custos, 'r', encoding='utf-8') as f_custos:
        leitor_csv = csv.DictReader(f_custos, delimiter=';')
        for linha in leitor_csv:
            # O Infracost CSV usa o nome do 'Arquivo Base' como 'ID do Caso'
            id_caso_infracost = linha['ID do Caso']
            custos[id_caso_infracost] = linha['Custo Mensal Total ($)']
else:
    print(f"[ERRO] O arquivo {arquivo_custos} não foi encontrado.")

dados_apendice_a = []

# 3. Ler o arquivo markdown de amostras e fundir com os custos
if os.path.exists(arquivo_amostras):
    with open(arquivo_amostras, 'r', encoding='utf-8') as f_amostras:
        for linha in f_amostras:
            linha = linha.strip()
            
            # Filtra as linhas da tabela Markdown
            # Ignoramos a linha de cabeçalho ('ID') e a de formatação ('---')
            if linha.startswith('|') and 'ID' not in linha and '---' not in linha:
                # Divide as colunas pelo separador pipe (|) e remove espaços extras
                colunas = [col.strip() for col in linha.split('|')][1:-1] 
                
                if len(colunas) == 6:
                    # CORREÇÃO: Pegando cada item pelo seu respectivo índice na lista!
                    id_caso = colunas[0]
                    arquivo_base = colunas[1]
                    complexidade = colunas[2]
                    regra_violada = colunas[3]
                    recursos_criados = colunas[4]
                    dependencias = colunas[5]
                    
                    # Busca o custo usando o Arquivo Base como chave (se não achar, retorna N/A)
                    custo_mensal = custos.get(arquivo_base, "N/A")
                    
                    dados_apendice_a.append({
                        'ID do Caso': id_caso,
                        'Arquivo Base': arquivo_base,
                        'Complexidade': complexidade,
                        'Regra Violada': regra_violada,
                        'Recursos Criados': recursos_criados,
                        'Dependências': dependencias,
                        'Custo Mensal ($)': custo_mensal
                    })
else:
    print(f"[ERRO] O arquivo {arquivo_amostras} não foi encontrado.")

# 4. Exportar os dados consolidados para um novo arquivo CSV
colunas_saida = ['ID do Caso', 'Arquivo Base', 'Complexidade', 'Regra Violada', 'Recursos Criados', 'Dependências', 'Custo Mensal ($)']

with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_saida:
    # Usando ponto e vírgula como delimitador para abrir facilmente no Excel
    escritor = csv.DictWriter(f_saida, fieldnames=colunas_saida, delimiter=';')
    escritor.writeheader()
    escritor.writerows(dados_apendice_a)

print(f"\n--- Estruturação do Apêndice A corrigida e concluída com sucesso! ---")
print(f"Os dados foram salvos em: {arquivo_saida}")