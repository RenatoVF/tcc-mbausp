#!/usr/bin/env python3
"""
Mede a consistencia do LLM entre execucoes repetidas do mesmo prompt, com
temperature=0 - que reduz, mas nao garante, determinismo. Compara N
matrizes de resultado do LLM, geradas por
N execucoes independentes de avaliador_llm.py + extrator_llm.py sobre o
mesmo conjunto de planos, e mede o quanto elas concordam entre si, regra a
regra e caso a caso.

Uso:
    python3 consistencia_repeticoes.py <caminho_para_o_set> <matriz_rep1.csv> <matriz_rep2.csv> [...]

As matrizes devem estar em <set>/analises/, no mesmo formato de
matriz_resultados_llm.csv (colunas ID do Caso;CKV_FINOPS_01;...;Veredito LLM).
Minimo de 2 repeticoes; o recomendado pelo orientador e 5.

Gera:
    <set>/analises/consistencia_repeticoes.csv    - taxa de consistencia por regra
    <set>/analises/discrepancias_repeticoes.csv   - casos/regras onde as repeticoes discordaram
"""
import csv
import sys
from pathlib import Path
from collections import Counter

REGRAS = ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"]


def normalizar_id(id_bruto):
    """Remove sufixos conhecidos (ex.: '.checkov') para casar entre matrizes."""
    id_bruto = id_bruto.strip()
    for sufixo in (".checkov", ".infracost", ".json"):
        if id_bruto.endswith(sufixo):
            id_bruto = id_bruto[: -len(sufixo)]
    return id_bruto


def ler_matriz(caminho):
    linhas = {}
    with caminho.open(encoding="utf-8") as f:
        leitor = csv.DictReader(f, delimiter=";")
        for linha in leitor:
            id_caso = normalizar_id(linha["ID do Caso"])
            linhas[id_caso] = linha
    return linhas


def main():
    if len(sys.argv) < 4:
        raise SystemExit(
            "Uso: python3 consistencia_repeticoes.py <caminho_para_o_set> <matriz_rep1.csv> <matriz_rep2.csv> [...]\n"
            "Minimo de 2 repeticoes (recomendado: 5). Os arquivos devem estar em <set>/analises/."
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    ANALISES_DIR = SET_ROOT / "analises"
    arquivos_repeticao = sys.argv[2:]

    repeticoes = []
    for nome_arquivo in arquivos_repeticao:
        caminho = ANALISES_DIR / nome_arquivo
        if not caminho.exists():
            raise SystemExit(f"Nao encontrei {caminho}")
        repeticoes.append(ler_matriz(caminho))

    n = len(repeticoes)
    ids_comuns = set(repeticoes[0])
    for rep in repeticoes[1:]:
        ids_comuns &= set(rep)
    ids_comuns = sorted(ids_comuns)

    if not ids_comuns:
        raise SystemExit("Nenhum ID de caso em comum entre as matrizes informadas.")

    linhas_resumo = []
    linhas_discrepancias = []

    for regra in REGRAS:
        pares_totais = 0
        pares_consistentes = 0
        for id_caso in ids_comuns:
            valores = [rep[id_caso].get(regra, "N/A") for rep in repeticoes]
            pares_totais += 1
            contagem = Counter(valores)
            valor_majoritario, freq_majoritaria = contagem.most_common(1)[0]
            if freq_majoritaria == n:
                pares_consistentes += 1
            else:
                linhas_discrepancias.append({
                    "Regra": regra,
                    "ID do Caso": id_caso,
                    "Valores nas repeticoes (na ordem informada)": " | ".join(valores),
                    "Valor majoritario": valor_majoritario,
                    "Frequencia do majoritario": f"{freq_majoritaria}/{n}",
                })
        taxa = pares_consistentes / pares_totais if pares_totais else None
        linhas_resumo.append({
            "Regra": regra,
            "Casos avaliados": pares_totais,
            "Casos 100% consistentes entre repeticoes": pares_consistentes,
            "Taxa de consistencia": f"{taxa:.3f}" if taxa is not None else "",
        })

    total_pares = sum(l["Casos avaliados"] for l in linhas_resumo)
    total_consistentes = sum(l["Casos 100% consistentes entre repeticoes"] for l in linhas_resumo)
    linhas_resumo.append({
        "Regra": "TODAS",
        "Casos avaliados": total_pares,
        "Casos 100% consistentes entre repeticoes": total_consistentes,
        "Taxa de consistencia": f"{(total_consistentes / total_pares):.3f}" if total_pares else "",
    })

    colunas_resumo = ["Regra", "Casos avaliados", "Casos 100% consistentes entre repeticoes", "Taxa de consistencia"]
    with (ANALISES_DIR / "consistencia_repeticoes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_resumo, delimiter=";")
        w.writeheader()
        w.writerows(linhas_resumo)

    colunas_disc = ["Regra", "ID do Caso", "Valores nas repeticoes (na ordem informada)", "Valor majoritario", "Frequencia do majoritario"]
    with (ANALISES_DIR / "discrepancias_repeticoes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_disc, delimiter=";")
        w.writeheader()
        w.writerows(linhas_discrepancias)

    print(f"OK: {n} repeticoes comparadas, {len(ids_comuns)} casos em comum.")
    print(f"Resumo salvo em {ANALISES_DIR / 'consistencia_repeticoes.csv'}")
    print(f"{len(linhas_discrepancias)} discrepancias detalhadas em {ANALISES_DIR / 'discrepancias_repeticoes.csv'}")


if __name__ == "__main__":
    main()
