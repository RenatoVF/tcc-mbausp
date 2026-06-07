import csv
import os

# 1. Definição dos caminhos dos arquivos
arquivo_amostras = 'amostras.md'
arquivo_checkov = 'matriz_resultados_checkov.csv'
arquivo_saida = 'apendice_c_matriz_checkov.csv'

# Dicionário de tradução para adequar o TCC ao idioma português
traducao = {
    "PASSED": "Aprovado",
    "FAILED": "Falhou",
    "N/A": "N/A"
}

# Dicionário para armazenar as avaliações do Checkov por Arquivo Base
resultados_checkov = {}

# 2. Ler o arquivo de resultados do Checkov
if os.path.exists(arquivo_checkov):
    with open(arquivo_checkov, 'r', encoding='utf-8') as f_checkov:
        leitor_csv = csv.DictReader(f_checkov, delimiter=';')
        for linha in leitor_csv:
            # Remove a extensão '.checkov' para que o ID bata exatamente com o Arquivo Base do Markdown
            id_caso_checkov = linha['ID do Caso'].replace('.checkov', '')
            resultados_checkov[id_caso_checkov] = linha
else:
    print(f"[ERRO] O arquivo {arquivo_checkov} não foi encontrado.")

dados_apendice_c = []

# 3. Ler o arquivo markdown de amostras e fundir com os resultados do Checkov
if os.path.exists(arquivo_amostras):
    with open(arquivo_amostras, 'r', encoding='utf-8') as f_amostras:
        for linha in f_amostras:
            linha = linha.strip()
            
            # Filtra as linhas da tabela Markdown
            if linha.startswith('|') and 'ID' not in linha and '---' not in linha:
                colunas = [col.strip() for col in linha.split('|')][1:-1] 
                
                if len(colunas) == 6:
                    id_caso = colunas[0]
                    arquivo_base = colunas[1]
                    
                    # Busca as avaliações usando o Arquivo Base como chave
                    avaliacao = resultados_checkov.get(arquivo_base, {})
                    
                    dados_apendice_c.append({
                        'ID do Caso': id_caso,
                        'CKV_FINOPS_01': traducao.get(avaliacao.get('CKV_FINOPS_01', 'N/A'), 'N/A'),
                        'CKV_FINOPS_02': traducao.get(avaliacao.get('CKV_FINOPS_02', 'N/A'), 'N/A'),
                        'CKV_FINOPS_03': traducao.get(avaliacao.get('CKV_FINOPS_03', 'N/A'), 'N/A'),
                        'CKV_FINOPS_04A': traducao.get(avaliacao.get('CKV_FINOPS_04A', 'N/A'), 'N/A'),
                        'CKV_FINOPS_04B': traducao.get(avaliacao.get('CKV_FINOPS_04B', 'N/A'), 'N/A'),
                        'Veredito Checkov': traducao.get(avaliacao.get('Veredito Checkov', 'N/A'), 'N/A')
                    })
else:
    print(f"[ERRO] O arquivo {arquivo_amostras} não foi encontrado.")

# 4. Exportar os dados consolidados para um novo arquivo CSV
colunas_saida = ['ID do Caso', 'CKV_FINOPS_01', 'CKV_FINOPS_02', 'CKV_FINOPS_03', 'CKV_FINOPS_04A', 'CKV_FINOPS_04B', 'Veredito Checkov']

with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_saida:
    escritor = csv.DictWriter(f_saida, fieldnames=colunas_saida, delimiter=';')
    escritor.writeheader()
    escritor.writerows(dados_apendice_c)

print(f"\n--- Estruturação do Apêndice C concluída com sucesso! ---")
print(f"Os dados foram salvos em: {arquivo_saida}")