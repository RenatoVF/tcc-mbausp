#!/usr/bin/env python3
"""
Testes estatisticos complementares as metricas por regra, parte viavel
sem a avaliacao humana:

  1. Teste de McNemar exato (binomial de sinal) comparando Checkov e LLM,
     por regra e agregado (pooled), sobre o par de classificacoes
     corretas/incorretas no MESMO conjunto de casos.
  2. Intervalo de confianca de 95% (bootstrap percentil, reamostragem de
     casos com reposicao) para Precision, Recall, F1 e Acuracia de cada
     avaliador, por regra e agregado.

O teste de Cochran's Q (comparando os 3 metodos simultaneamente) e a
medida de concordancia entre os 3 avaliadores humanos (ex.: Kappa de
Fleiss) dependem da matriz de resultados humanos (ainda pendente de
coleta) e NAO sao calculados aqui.

Convencao de N/A (importante, replica exatamente a de metricas_por_regra.py):
um caso so entra na matriz de confusao (TP/FP/FN/TN) de um avaliador
quando tanto o ground truth quanto a resposta daquele avaliador sao
PASSED/FAILED (nenhum dos dois e N/A). Quando um dos dois e N/A e o outro
nao, o caso e uma "divergencia de aplicabilidade" e fica de fora tanto do
numerador quanto do denominador das 4 metricas - exatamente como ja
reportado em metricas_por_regra.csv (coluna "Divergencias N/A"). Para o
teste de McNemar (pareado por definicao), usamos a INTERSECCAO das
populacoes aplicaveis de Checkov e LLM, e reportamos ao lado quantas
divergencias de N/A cada avaliador teve naquela regra, para que uma regra
sem pares discordantes nao seja lida como "sem erro nenhum" quando na
verdade so a divergencia era de aplicabilidade (ex.: CKV_FINOPS_03 no LLM).

Uso:
    python3 testes_estatisticos.py <caminho_para_o_set>

Gera:
    <set>/analises/mcnemar_checkov_vs_llm.csv
    <set>/analises/intervalos_confianca.csv
"""
import csv
import math
import random
import sys
from pathlib import Path

REGRAS = ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"]
SEED_BOOTSTRAP = 20260901
N_BOOTSTRAP = 10000


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


def classificar(gt_valor, av_valor):
    """Retorna 'tp'|'fp'|'fn'|'tn'|'na' (na = divergencia de aplicabilidade,
    excluida da matriz de confusao, igual a metricas_por_regra.py)."""
    if gt_valor == "N/A" or av_valor == "N/A":
        return "na"
    if gt_valor == "FAILED" and av_valor == "FAILED":
        return "tp"
    if gt_valor == "PASSED" and av_valor == "PASSED":
        return "tn"
    if gt_valor == "PASSED" and av_valor == "FAILED":
        return "fp"
    if gt_valor == "FAILED" and av_valor == "PASSED":
        return "fn"
    raise ValueError(f"valor inesperado: gt={gt_valor} av={av_valor}")


def calcular_metricas(tp, fp, fn, tn):
    total = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall and (precision + recall) > 0) else None
    accuracy = (tp + tn) / total if total else None
    return precision, recall, f1, accuracy


def binom_cdf(k, n, p=0.5):
    return sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(0, k + 1))


def mcnemar_exato(b, c):
    """McNemar exato (teste binomial de sinal) para pares discordantes b, c.
    Retorna p-valor bicaudal, ou None se nao houver nenhum par discordante."""
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    return min(2 * binom_cdf(k, n, 0.5), 1.0)


def percentil(lista, p):
    if not lista:
        return None
    s = sorted(lista)
    idx = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[idx]


def bootstrap_ci(pares_tipo, rng, n_rep=N_BOOTSTRAP):
    """pares_tipo: lista de classificacoes ja resolvidas ('tp'/'fp'/'fn'/'tn'),
    isto e, a populacao ja restrita (sem 'na'). Retorna IC 95% percentil
    para precision/recall/f1/accuracy via reamostragem com reposicao."""
    n = len(pares_tipo)
    amostras = {"precision": [], "recall": [], "f1": [], "accuracy": []}
    if n == 0:
        return {k: (None, None) for k in amostras}
    for _ in range(n_rep):
        tp = fp = fn = tn = 0
        for _ in range(n):
            tipo = pares_tipo[rng.randrange(n)]
            if tipo == "tp":
                tp += 1
            elif tipo == "fp":
                fp += 1
            elif tipo == "fn":
                fn += 1
            elif tipo == "tn":
                tn += 1
        precision, recall, f1, accuracy = calcular_metricas(tp, fp, fn, tn)
        for nome, valor in (("precision", precision), ("recall", recall), ("f1", f1), ("accuracy", accuracy)):
            if valor is not None:
                amostras[nome].append(valor)
    return {nome: (percentil(vals, 0.025), percentil(vals, 0.975)) for nome, vals in amostras.items()}


def fmt(x):
    return "" if x is None else f"{x:.3f}"


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 testes_estatisticos.py <caminho_para_o_set>\n"
            "Exemplos: python3 testes_estatisticos.py ../../training_set\n"
            "          python3 testes_estatisticos.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    ANALISES_DIR = SET_ROOT / "analises"
    GT_CSV = ANALISES_DIR / "ground_truth_regras.csv"
    CHECKOV_CSV = ANALISES_DIR / "matriz_resultados_checkov.csv"
    LLM_CSV = ANALISES_DIR / "matriz_resultados_llm.csv"

    for caminho in (GT_CSV, CHECKOV_CSV, LLM_CSV):
        if not caminho.exists():
            raise SystemExit(f"Nao encontrei {caminho}.")

    ground_truth = ler_matriz(GT_CSV)
    checkov = ler_matriz(CHECKOV_CSV)
    llm = ler_matriz(LLM_CSV)

    ids_comuns = sorted(set(ground_truth) & set(checkov) & set(llm))

    rng = random.Random(SEED_BOOTSTRAP)

    linhas_mcnemar = []
    linhas_ic = []

    # acumuladores para o agregado (pooled) - populacao propria de cada avaliador
    # (mesma logica de metricas_por_regra.py: exclui casos 'na' por avaliador)
    pooled_tipos = {"Checkov": [], "LLM": []}
    # populacao conjunta (interseccao) para o McNemar agregado
    pooled_correto = {"Checkov": [], "LLM": []}
    pooled_na_div = {"Checkov": 0, "LLM": 0}

    for regra in REGRAS:
        tipos_regra = {"Checkov": [], "LLM": []}
        na_div_regra = {"Checkov": 0, "LLM": 0}
        correto_conjunto = {"Checkov": [], "LLM": []}  # so casos aplicaveis aos DOIS avaliadores

        for id_caso in ids_comuns:
            gt_valor = ground_truth[id_caso].get(regra, "N/A")
            ck_valor = checkov[id_caso].get(regra, "N/A")
            llm_valor = llm[id_caso].get(regra, "N/A")

            tipo_ck = classificar(gt_valor, ck_valor)
            tipo_llm = classificar(gt_valor, llm_valor)

            if tipo_ck != "na":
                tipos_regra["Checkov"].append(tipo_ck)
                pooled_tipos["Checkov"].append(tipo_ck)
            elif gt_valor != ck_valor:
                # divergencia real de aplicabilidade (um dos dois e N/A, o outro nao)
                # - nao conta os casos em que ambos corretamente dizem N/A
                na_div_regra["Checkov"] += 1
                pooled_na_div["Checkov"] += 1

            if tipo_llm != "na":
                tipos_regra["LLM"].append(tipo_llm)
                pooled_tipos["LLM"].append(tipo_llm)
            elif gt_valor != llm_valor:
                na_div_regra["LLM"] += 1
                pooled_na_div["LLM"] += 1

            # McNemar: so entra na populacao pareada se NENHUM dos dois teve 'na'
            if tipo_ck != "na" and tipo_llm != "na":
                correto_ck = tipo_ck in ("tp", "tn")
                correto_llm = tipo_llm in ("tp", "tn")
                correto_conjunto["Checkov"].append(correto_ck)
                correto_conjunto["LLM"].append(correto_llm)
                pooled_correto["Checkov"].append(correto_ck)
                pooled_correto["LLM"].append(correto_llm)

        n_pareado = len(correto_conjunto["Checkov"])
        b = sum(1 for ck, l in zip(correto_conjunto["Checkov"], correto_conjunto["LLM"]) if ck and not l)
        c = sum(1 for ck, l in zip(correto_conjunto["Checkov"], correto_conjunto["LLM"]) if not ck and l)
        p_valor = mcnemar_exato(b, c)

        linhas_mcnemar.append({
            "Regra": regra,
            "N (pares aplicaveis a ambos)": n_pareado,
            "Checkov correto / LLM incorreto (b)": b,
            "Checkov incorreto / LLM correto (c)": c,
            "Divergencias N/A - Checkov": na_div_regra["Checkov"],
            "Divergencias N/A - LLM": na_div_regra["LLM"],
            "p-valor (McNemar exato)": "" if p_valor is None else f"{p_valor:.4f}",
            "Significativo (alfa=0,05)": ("Nao aplicavel (sem pares discordantes)" if p_valor is None
                                           else ("Sim" if p_valor < 0.05 else "Nao")),
        })

        for rotulo in ("Checkov", "LLM"):
            ic = bootstrap_ci(tipos_regra[rotulo], rng)
            tp = tipos_regra[rotulo].count("tp")
            fp = tipos_regra[rotulo].count("fp")
            fn = tipos_regra[rotulo].count("fn")
            tn = tipos_regra[rotulo].count("tn")
            precision, recall, f1, accuracy = calcular_metricas(tp, fp, fn, tn)
            linhas_ic.append({
                "Avaliador": rotulo, "Regra": regra, "N": len(tipos_regra[rotulo]),
                "Precision": fmt(precision), "Precision IC95%": f"[{fmt(ic['precision'][0])}, {fmt(ic['precision'][1])}]",
                "Recall": fmt(recall), "Recall IC95%": f"[{fmt(ic['recall'][0])}, {fmt(ic['recall'][1])}]",
                "F1": fmt(f1), "F1 IC95%": f"[{fmt(ic['f1'][0])}, {fmt(ic['f1'][1])}]",
                "Accuracy": fmt(accuracy), "Accuracy IC95%": f"[{fmt(ic['accuracy'][0])}, {fmt(ic['accuracy'][1])}]",
            })

    # ---- agregado (pooled) ----
    n_pareado_pool = len(pooled_correto["Checkov"])
    b_pool = sum(1 for ck, l in zip(pooled_correto["Checkov"], pooled_correto["LLM"]) if ck and not l)
    c_pool = sum(1 for ck, l in zip(pooled_correto["Checkov"], pooled_correto["LLM"]) if not ck and l)
    p_valor_pool = mcnemar_exato(b_pool, c_pool)
    linhas_mcnemar.append({
        "Regra": "TODAS (pooled)",
        "N (pares aplicaveis a ambos)": n_pareado_pool,
        "Checkov correto / LLM incorreto (b)": b_pool,
        "Checkov incorreto / LLM correto (c)": c_pool,
        "Divergencias N/A - Checkov": pooled_na_div["Checkov"],
        "Divergencias N/A - LLM": pooled_na_div["LLM"],
        "p-valor (McNemar exato)": "" if p_valor_pool is None else f"{p_valor_pool:.4f}",
        "Significativo (alfa=0,05)": ("Nao aplicavel (sem pares discordantes)" if p_valor_pool is None
                                       else ("Sim" if p_valor_pool < 0.05 else "Nao")),
    })

    for rotulo in ("Checkov", "LLM"):
        ic = bootstrap_ci(pooled_tipos[rotulo], rng)
        tp = pooled_tipos[rotulo].count("tp")
        fp = pooled_tipos[rotulo].count("fp")
        fn = pooled_tipos[rotulo].count("fn")
        tn = pooled_tipos[rotulo].count("tn")
        precision, recall, f1, accuracy = calcular_metricas(tp, fp, fn, tn)
        linhas_ic.append({
            "Avaliador": rotulo, "Regra": "TODAS (pooled)", "N": len(pooled_tipos[rotulo]),
            "Precision": fmt(precision), "Precision IC95%": f"[{fmt(ic['precision'][0])}, {fmt(ic['precision'][1])}]",
            "Recall": fmt(recall), "Recall IC95%": f"[{fmt(ic['recall'][0])}, {fmt(ic['recall'][1])}]",
            "F1": fmt(f1), "F1 IC95%": f"[{fmt(ic['f1'][0])}, {fmt(ic['f1'][1])}]",
            "Accuracy": fmt(accuracy), "Accuracy IC95%": f"[{fmt(ic['accuracy'][0])}, {fmt(ic['accuracy'][1])}]",
        })

    colunas_mcnemar = ["Regra", "N (pares aplicaveis a ambos)", "Checkov correto / LLM incorreto (b)",
                        "Checkov incorreto / LLM correto (c)", "Divergencias N/A - Checkov",
                        "Divergencias N/A - LLM", "p-valor (McNemar exato)", "Significativo (alfa=0,05)"]
    with (ANALISES_DIR / "mcnemar_checkov_vs_llm.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_mcnemar, delimiter=";")
        w.writeheader()
        w.writerows(linhas_mcnemar)

    colunas_ic = ["Avaliador", "Regra", "N", "Precision", "Precision IC95%", "Recall", "Recall IC95%",
                  "F1", "F1 IC95%", "Accuracy", "Accuracy IC95%"]
    with (ANALISES_DIR / "intervalos_confianca.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_ic, delimiter=";")
        w.writeheader()
        w.writerows(linhas_ic)

    print(f"OK: McNemar salvo em {ANALISES_DIR / 'mcnemar_checkov_vs_llm.csv'}")
    print(f"OK: Intervalos de confianca salvos em {ANALISES_DIR / 'intervalos_confianca.csv'}")


if __name__ == "__main__":
    main()
