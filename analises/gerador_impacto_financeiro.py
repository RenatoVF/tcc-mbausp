import csv
import os

arquivo_entrada = 'apendice_a_matriz_amostra.csv'
arquivo_saida = 'dados_grafico_impacto_financeiro.csv'

custos_c = {}
custos_nc = {}

# 1. Leitura dos dados do Apêndice A
if os.path.exists(arquivo_entrada):
    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        leitor = csv.DictReader(f, delimiter=';')
        for linha in leitor:
            id_caso = linha['ID do Caso']
            # Converte a vírgula de volta para ponto para fazer o cálculo matemático
            custo_str = linha['Custo Mensal ($)'].replace(',', '.')
            custo = float(custo_str) if custo_str != 'N/A' else 0.0
            
            # Separa os casos Conformes (C) dos Não Conformes (NC) usando o número do caso
            if id_caso.startswith('NC'):
                num_caso = id_caso.replace('NC', '')
                custos_nc[num_caso] = custo
            else:
                num_caso = id_caso.replace('C', '')
                custos_c[num_caso] = custo

# 2. Aplicação da Fórmula: IF = CNC - CC
dados_grafico = []
for num_caso in sorted(custos_c.keys()):
    cc = custos_c[num_caso]
    cnc = custos_nc.get(num_caso, 0.0)
    
    # Aplica a equação definida na metodologia
    impacto_financeiro = cnc - cc
    
    # Prepara os dados convertendo o ponto de volta para vírgula (padrão PT-BR)
    dados_grafico.append({
        'Par de Cenários': f'Par {num_caso}',
        'Custo Conforme (CC)': str(round(cc, 2)).replace('.', ','),
        'Custo Não Conforme (CNC)': str(round(cnc, 2)).replace('.', ','),
        'Impacto Financeiro (IF)': str(round(impacto_financeiro, 2)).replace('.', ',')
    })

# 3. Exportação para o Excel
colunas = ['Par de Cenários', 'Custo Conforme (CC)', 'Custo Não Conforme (CNC)', 'Impacto Financeiro (IF)']
with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_out:
    escritor = csv.DictWriter(f_out, fieldnames=colunas, delimiter=';')
    escritor.writeheader()
    escritor.writerows(dados_grafico)

print(f"Dados financeiros calculados com sucesso! Arquivo salvo em: {arquivo_saida}")