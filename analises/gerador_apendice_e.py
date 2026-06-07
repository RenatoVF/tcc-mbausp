import csv
import os

# 1. Definição dos caminhos dos arquivos
arquivo_amostras = 'amostras.md'
arquivo_llm = 'matriz_resultados_llm.csv'
arquivo_saida = 'apendice_e_matriz_llm.csv'

# Dicionário de tradução para adequar o TCC ao idioma português
traducao = {
    "PASSED": "Aprovado",
    "FAILED": "Falhou",
    "N/A": "N/A"
}

# Dicionário para armazenar as avaliações do LLM por Arquivo Base
resultados_llm = {}

# 2. Ler o arquivo de resultados do LLM
if os.path.exists(arquivo_llm):
    with open(arquivo_llm, 'r', encoding='utf-8') as f_llm:
        leitor_csv = csv.DictReader(f_llm, delimiter=';')
        for linha in leitor_csv:
            # O ID do Caso no CSV do LLM já corresponde ao Arquivo Base do Markdown
            id_caso_llm = linha['ID do Caso']
            resultados_llm[id_caso_llm] = linha
else:
    print(f"[ERRO] O arquivo {arquivo_llm} não foi encontrado.")

dados_apendice_e = []

# 3. Ler o arquivo markdown de amostras e fundir com os resultados do LLM
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
                    id_caso = colunas[0]
                    arquivo_base = colunas[1]
                    
                    # Busca as avaliações da IA usando o Arquivo Base como chave
                    avaliacao = resultados_llm.get(arquivo_base, {})
                    
                    dados_apendice_e.append({
                        'ID do Caso': id_caso,
                        'CKV_FINOPS_01': traducao.get(avaliacao.get('CKV_FINOPS_01', 'N/A'), 'N/A'),
                        'CKV_FINOPS_02': traducao.get(avaliacao.get('CKV_FINOPS_02', 'N/A'), 'N/A'),
                        'CKV_FINOPS_03': traducao.get(avaliacao.get('CKV_FINOPS_03', 'N/A'), 'N/A'),
                        'CKV_FINOPS_04A': traducao.get(avaliacao.get('CKV_FINOPS_04A', 'N/A'), 'N/A'),
                        'CKV_FINOPS_04B': traducao.get(avaliacao.get('CKV_FINOPS_04B', 'N/A'), 'N/A'),
                        'Veredito LLM': traducao.get(avaliacao.get('Veredito LLM', 'N/A'), 'N/A')
                    })
else:
    print(f"[ERRO] O arquivo {arquivo_amostras} não foi encontrado.")

# 4. Exportar os dados consolidados para um novo arquivo CSV
colunas_saida = ['ID do Caso', 'CKV_FINOPS_01', 'CKV_FINOPS_02', 'CKV_FINOPS_03', 'CKV_FINOPS_04A', 'CKV_FINOPS_04B', 'Veredito LLM']

with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_saida:
    escritor = csv.DictWriter(f_saida, fieldnames=colunas_saida, delimiter=';')
    escritor.writeheader()
    escritor.writerows(dados_apendice_e)

print(f"\n--- Estruturação do Apêndice E concluída com sucesso! ---")
print(f"Os dados foram salvos em: {arquivo_saida}")