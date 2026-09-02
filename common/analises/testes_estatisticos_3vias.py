#!/usr/bin/env python3
"""
Testes estatisticos de 3 vias (Checkov, LLM, Humano), habilitados quando
matriz_resultados_humanos.csv existir:

  1. Teste de Cochran's Q - teste global comparando as 3 proporcoes de
     acerto simultaneamente, por regra e agregado (pooled). Como o numero
     de metodos e fixo em k=3, os graus de liberdade sao sempre k-1=2, e a
     distribuicao qui-quadrado com 2 graus de liberdade tem forma fechada
     conhecida (CDF = 1 - exp(-x/2)); por isso o p-valor e calculado
     diretamente por exp(-Q/2), sem depender de scipy.
  2. McNemar exato par a par (Checkov x LLM, Checkov x Humano, LLM x
     Humano) como pos-teste, com correcao de Holm-Bonferroni para as 3
     comparacoes multiplas, por regra e agregado.

O McNemar Checkov x LLM aqui e redundante com testes_estatisticos.py (que
ja o calcula isoladamente); ele e recalculado aqui apenas para poder entrar
no mesmo procedimento de correcao de Holm-Bonferroni junto com os outros
2 pares - nao substitui o arquivo mcnemar_checkov_vs_llm.csv ja existente.

Convencao de N/A: identica a metricas_por_regra.py e testes_estatisticos.py
(um caso so entra na matriz de confusao de um avaliador quando o ground
truth e a resposta do avaliador sao ambos PASSED/FAILED). Para o Humano,
o valor "SEM_MAIORIA" (matriz_resultados_humanos.csv, quando os 3
avaliadores discordam totalmente) e tratado da mesma forma que N/A aqui -
o caso fica fora da populacao aplicavel para aquela regra.

Uso:
    python3 testes_estatisticos_3vias.py <caminho_para_o_set>

Gera:
    <set>/analises/cochrans_q.csv
    <set>/analises/mcnemar_3vias_pareado.csv
"""
import csv
import math
import sys
from pathlib import Path

REGRAS = ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"]
METODOS = ["Checkov", "LLM", "Humano"]
PARES = [("Checkov", "LLM"), ("Checkov", "Humano"), ("LLM", "Humano")]

VALORES_NAO_APLICAVEIS = {"N/A", "SEM_MAIORIA", ""}


def normalizar_id(id_bruto):
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


def correto(gt_valor, av_valor):
    """True/False se av_valor acerta o ground truth, None se algum dos
    dois for N/A/SEM_MAIORIA/vazio (caso fora da populacao aplicavel)."""
    if gt_valor in VALORES_NAO_APLICAVEIS or av_valor in VALORES_NAO_APLICAVEIS:
        return None
    if gt_valor not in ("PASSED", "FAILED") or av_valor not in ("PASSED", "FAILED"):
        return None
    return gt_valor == av_valor


def binom_cdf(k, n, p=0.5):
    return sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(0, k + 1))


def mcnemar_exato(b, c):
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    return min(2 * binom_cdf(k, n, 0.5), 1.0)


def holm_bonferroni(pares_pvalor, alfa=0.05):
    """pares_pvalor: lista de (rotulo, p_valor_ou_None). Retorna dict
    {rotulo: (p_ajustado_ou_None, significativo_bool_ou_None)} seguindo o
    procedimento step-down de Holm: ordena por p-valor crescente, compara
    p(i) a alfa/(m-i+1); uma vez que uma hipotese nao e rejeitada, todas as
    seguintes (p-valor maior) tambem nao sao, mesmo que seu proprio limiar
    individual seria superado."""
    validos = [(r, p) for r, p in pares_pvalor if p is not None]
    m = len(validos)
    resultado = {r: (None, None) for r, p in pares_pvalor if p is None}
    if m == 0:
        return resultado

    validos.sort(key=lambda x: x[1])
    rejeitar_daqui_pra_frente = True
    for i, (rotulo, p) in enumerate(validos):
        limiar = alfa / (m - i)
        significativo = rejeitar_daqui_pra_frente and (p < limiar)
        if not significativo:
            rejeitar_daqui_pra_frente = False
        resultado[rotulo] = (p, significativo)
    return resultado


def cochrans_q(matriz_corretos):
    """matriz_corretos: lista de listas [c_checkov, c_llm, c_humano] (0/1)
    por caso, ja restrita a casos aplicaveis aos 3 metodos simultaneamente.
    Retorna (Q, p_valor) ou (None, None) se nao aplicavel."""
    N = len(matriz_corretos)
    k = len(METODOS)
    if N == 0:
        return None, None

    Cj = [sum(linha[j] for linha in matriz_corretos) for j in range(k)]
    Ri = [sum(linha) for linha in matriz_corretos]
    C_bar = sum(Cj) / k

    denom = k * sum(Ri) - sum(r ** 2 for r in Ri)
    if denom == 0:
        return None, None  # sem variabilidade (todos os metodos sempre concordam em cada caso)

    numerador = k * (k - 1) * sum((c - C_bar) ** 2 for c in Cj)
    Q = numerador / denom
    # df = k - 1 = 2 (fixo, ver docstring) -> p-valor em forma fechada
    p_valor = math.exp(-Q / 2)
    return Q, p_valor


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 testes_estatisticos_3vias.py <caminho_para_o_set>\n"
            "Exemplos: python3 testes_estatisticos_3vias.py ../../training_set\n"
            "          python3 testes_estatisticos_3vias.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    ANALISES_DIR = SET_ROOT / "analises"
    GT_CSV = ANALISES_DIR / "ground_truth_regras.csv"
    CHECKOV_CSV = ANALISES_DIR / "matriz_resultados_checkov.csv"
    LLM_CSV = ANALISES_DIR / "matriz_resultados_llm.csv"
    HUMANO_CSV = ANALISES_DIR / "matriz_resultados_humanos.csv"

    for caminho in (GT_CSV, CHECKOV_CSV, LLM_CSV):
        if not caminho.exists():
            raise SystemExit(f"Nao encontrei {caminho}.")
    if not HUMANO_CSV.exists():
        raise SystemExit(
            f"Nao encontrei {HUMANO_CSV}. Rode extrator_revisao_humana.py "
            "(em common/revisao_humana/) primeiro para gerar a matriz humana deste set."
        )

    ground_truth = ler_matriz(GT_CSV)
    matrizes = {"Checkov": ler_matriz(CHECKOV_CSV), "LLM": ler_matriz(LLM_CSV), "Humano": ler_matriz(HUMANO_CSV)}
    ids_comuns = sorted(set(ground_truth) & set(matrizes["Checkov"]) & set(matrizes["LLM"]) & set(matrizes["Humano"]))

    linhas_q = []
    linhas_mcnemar = []

    pool_corretos = {m: [] for m in METODOS}  # para o Q agregado: [c_checkov, c_llm, c_humano] por (caso, regra)
    pool_pares_corretos = {par: {"a": [], "b": []} for par in PARES}  # populacao propria de cada par, pooled

    for regra in REGRAS:
        linha_corretos = []  # matriz N x 3 para o Q desta regra
        pares_corretos_regra = {par: {"a": [], "b": []} for par in PARES}
        contagem_corretos = {m: 0 for m in METODOS}
        N_por_metodo = {m: 0 for m in METODOS}

        for id_caso in ids_comuns:
            gt_valor = ground_truth[id_caso].get(regra, "N/A")
            resultados_caso = {m: correto(gt_valor, matrizes[m][id_caso].get(regra, "N/A")) for m in METODOS}

            for m in METODOS:
                if resultados_caso[m] is not None:
                    N_por_metodo[m] += 1
                    if resultados_caso[m]:
                        contagem_corretos[m] += 1

            # Cochran's Q exige design totalmente cruzado: so entra se os 3 tiverem resultado aplicavel
            if all(v is not None for v in resultados_caso.values()):
                vetor = [int(resultados_caso[m]) for m in METODOS]
                linha_corretos.append(vetor)
                pool_corretos_linha = dict(zip(METODOS, vetor))
                for m in METODOS:
                    pool_corretos[m].append(pool_corretos_linha[m])

            for par in PARES:
                a, b = par
                if resultados_caso[a] is not None and resultados_caso[b] is not None:
                    pares_corretos_regra[par]["a"].append(resultados_caso[a])
                    pares_corretos_regra[par]["b"].append(resultados_caso[b])
                    pool_pares_corretos[par]["a"].append(resultados_caso[a])
                    pool_pares_corretos[par]["b"].append(resultados_caso[b])

        Q, p_q = cochrans_q(linha_corretos)
        linhas_q.append({
            "Regra": regra,
            "N (aplicavel aos 3 metodos)": len(linha_corretos),
            "Checkov corretos": contagem_corretos["Checkov"], "Checkov N": N_por_metodo["Checkov"],
            "LLM corretos": contagem_corretos["LLM"], "LLM N": N_por_metodo["LLM"],
            "Humano corretos": contagem_corretos["Humano"], "Humano N": N_por_metodo["Humano"],
            "Q": "" if Q is None else f"{Q:.4f}",
            "gl": "" if Q is None else 2,
            "p-valor": "" if p_q is None else f"{p_q:.4f}",
            "Significativo (alfa=0,05)": ("Nao aplicavel" if p_q is None else ("Sim" if p_q < 0.05 else "Nao")),
        })

        pvalores_regra = []
        for par in PARES:
            a_vals, b_vals = pares_corretos_regra[par]["a"], pares_corretos_regra[par]["b"]
            n_par = len(a_vals)
            b_disc = sum(1 for x, y in zip(a_vals, b_vals) if x and not y)
            c_disc = sum(1 for x, y in zip(a_vals, b_vals) if not x and y)
            p = mcnemar_exato(b_disc, c_disc)
            pvalores_regra.append((f"{par[0]} x {par[1]}", p, n_par, b_disc, c_disc))

        ajustes = holm_bonferroni([(rotulo, p) for rotulo, p, _, _, _ in pvalores_regra])
        for rotulo, p, n_par, b_disc, c_disc in pvalores_regra:
            p_ajustado, significativo = ajustes[rotulo]
            linhas_mcnemar.append({
                "Regra": regra, "Par": rotulo, "N (pares aplicaveis)": n_par,
                "Discordantes (a-sim/b-nao)": b_disc, "Discordantes (a-nao/b-sim)": c_disc,
                "p-valor bruto": "" if p is None else f"{p:.4f}",
                "p-valor (Holm-Bonferroni)": "" if p_ajustado is None else f"{p_ajustado:.4f}",
                "Significativo apos correcao (alfa=0,05)": (
                    "Nao aplicavel (sem pares discordantes)" if p is None
                    else ("Sim" if significativo else "Nao")
                ),
            })

    # ---- agregado (pooled) ----
    linha_pool = list(zip(pool_corretos["Checkov"], pool_corretos["LLM"], pool_corretos["Humano"]))
    Q_pool, p_q_pool = cochrans_q([list(t) for t in linha_pool])
    linhas_q.append({
        "Regra": "TODAS (pooled)",
        "N (aplicavel aos 3 metodos)": len(linha_pool),
        "Checkov corretos": sum(pool_corretos["Checkov"]), "Checkov N": len(pool_corretos["Checkov"]),
        "LLM corretos": sum(pool_corretos["LLM"]), "LLM N": len(pool_corretos["LLM"]),
        "Humano corretos": sum(pool_corretos["Humano"]), "Humano N": len(pool_corretos["Humano"]),
        "Q": "" if Q_pool is None else f"{Q_pool:.4f}",
        "gl": "" if Q_pool is None else 2,
        "p-valor": "" if p_q_pool is None else f"{p_q_pool:.4f}",
        "Significativo (alfa=0,05)": ("Nao aplicavel" if p_q_pool is None else ("Sim" if p_q_pool < 0.05 else "Nao")),
    })

    pvalores_pool = []
    for par in PARES:
        a_vals, b_vals = pool_pares_corretos[par]["a"], pool_pares_corretos[par]["b"]
        n_par = len(a_vals)
        b_disc = sum(1 for x, y in zip(a_vals, b_vals) if x and not y)
        c_disc = sum(1 for x, y in zip(a_vals, b_vals) if not x and y)
        p = mcnemar_exato(b_disc, c_disc)
        pvalores_pool.append((f"{par[0]} x {par[1]}", p, n_par, b_disc, c_disc))

    ajustes_pool = holm_bonferroni([(rotulo, p) for rotulo, p, _, _, _ in pvalores_pool])
    for rotulo, p, n_par, b_disc, c_disc in pvalores_pool:
        p_ajustado, significativo = ajustes_pool[rotulo]
        linhas_mcnemar.append({
            "Regra": "TODAS (pooled)", "Par": rotulo, "N (pares aplicaveis)": n_par,
            "Discordantes (a-sim/b-nao)": b_disc, "Discordantes (a-nao/b-sim)": c_disc,
            "p-valor bruto": "" if p is None else f"{p:.4f}",
            "p-valor (Holm-Bonferroni)": "" if p_ajustado is None else f"{p_ajustado:.4f}",
            "Significativo apos correcao (alfa=0,05)": (
                "Nao aplicavel (sem pares discordantes)" if p is None
                else ("Sim" if significativo else "Nao")
            ),
        })

    colunas_q = ["Regra", "N (aplicavel aos 3 metodos)", "Checkov corretos", "Checkov N",
                 "LLM corretos", "LLM N", "Humano corretos", "Humano N", "Q", "gl", "p-valor",
                 "Significativo (alfa=0,05)"]
    with (ANALISES_DIR / "cochrans_q.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_q, delimiter=";")
        w.writeheader()
        w.writerows(linhas_q)

    colunas_mcnemar = ["Regra", "Par", "N (pares aplicaveis)", "Discordantes (a-sim/b-nao)",
                        "Discordantes (a-nao/b-sim)", "p-valor bruto", "p-valor (Holm-Bonferroni)",
                        "Significativo apos correcao (alfa=0,05)"]
    with (ANALISES_DIR / "mcnemar_3vias_pareado.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_mcnemar, delimiter=";")
        w.writeheader()
        w.writerows(linhas_mcnemar)

    print(f"OK: Cochran's Q salvo em {ANALISES_DIR / 'cochrans_q.csv'}")
    print(f"OK: McNemar pareado (3 vias, Holm-Bonferroni) salvo em {ANALISES_DIR / 'mcnemar_3vias_pareado.csv'}")


if __name__ == "__main__":
    main()
