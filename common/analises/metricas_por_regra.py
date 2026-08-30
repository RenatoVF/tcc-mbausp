#!/usr/bin/env python3
"""
Calcula Precision, Recall, F1 e Acuracia POR REGRA (nao so o veredito
agregado do plano), cruzando o ground truth independente
(ground_truth_regras.csv, gerado por gerar_ground_truth.py) com as
matrizes de resultado de cada avaliador disponivel no conjunto
(Checkov, LLM e, quando existir, avaliacao humana).

Classe positiva = FAILED (nao conformidade), conforme a revisao do
orientador (nao usar "precisao" como sinonimo de "acuracia": as 4
metricas sao reportadas separadamente).

Uso:
    python3 metricas_por_regra.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/analises/):
    python3 metricas_por_regra.py ../../training_set
    python3 metricas_por_regra.py ../../test_set

Gera:
    <set>/analises/metricas_por_regra.csv       - Precision/Recall/F1/Acuracia por (avaliador, regra)
    <set>/analises/discrepancias_por_regra.csv  - casos especificos onde o avaliador errou uma regra
"""
import csv
import sys
from pathlib import Path

REGRAS = ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"]

# nome do arquivo -> (rotulo do avaliador, coluna de veredito agregado no arquivo)
FONTES = {
    "matriz_resultados_checkov.csv": "Checkov",
    "matriz_resultados_llm.csv": "LLM",
    "matriz_resultados_humanos.csv": "Humano",
}


def normalizar_id(id_bruto):
    """Remove sufixos conhecidos (ex.: '.checkov') para casar com o ground truth."""
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


def calcular_metricas(tp, fp, fn, tn):
    total = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall and (precision + recall) > 0) else None
    accuracy = (tp + tn) / total if total else None
    return precision, recall, f1, accuracy


def fmt(x):
    return "" if x is None else f"{x:.3f}"


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 metricas_por_regra.py <caminho_para_o_set>\n"
            "Exemplos: python3 metricas_por_regra.py ../../training_set\n"
            "          python3 metricas_por_regra.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    ANALISES_DIR = SET_ROOT / "analises"
    GT_CSV = ANALISES_DIR / "ground_truth_regras.csv"

    if not GT_CSV.exists():
        raise SystemExit(f"Nao encontrei {GT_CSV}. Rode gerar_ground_truth.py primeiro para este set.")

    ground_truth = ler_matriz(GT_CSV)

    fontes_disponiveis = {}
    for nome_arquivo, rotulo in FONTES.items():
        caminho = ANALISES_DIR / nome_arquivo
        if caminho.exists():
            fontes_disponiveis[rotulo] = ler_matriz(caminho)

    if not fontes_disponiveis:
        raise SystemExit(f"Nenhuma matriz de resultado encontrada em {ANALISES_DIR} (Checkov/LLM/Humano).")

    linhas_metricas = []
    linhas_discrepancias = []

    for rotulo, matriz in fontes_disponiveis.items():
        ids_comuns = sorted(set(ground_truth) & set(matriz))
        ids_faltando_no_avaliador = sorted(set(ground_truth) - set(matriz))
        if ids_faltando_no_avaliador:
            print(f"[AVISO] {rotulo}: {len(ids_faltando_no_avaliador)} casos do ground truth nao encontrados na matriz "
                  f"(ex.: {ids_faltando_no_avaliador[:3]})")

        for regra in REGRAS:
            tp = fp = fn = tn = 0
            na_mismatches = 0
            for id_caso in ids_comuns:
                gt_valor = ground_truth[id_caso].get(regra, "N/A")
                av_valor = matriz[id_caso].get(regra, "N/A")

                if gt_valor == "N/A" or av_valor == "N/A":
                    if gt_valor != av_valor:
                        na_mismatches += 1
                        linhas_discrepancias.append({
                            "Avaliador": rotulo, "Regra": regra, "ID do Caso": id_caso,
                            "Ground Truth": gt_valor, "Resultado Avaliador": av_valor,
                            "Tipo": "Divergencia de aplicabilidade (N/A)",
                        })
                    continue

                if gt_valor == "FAILED" and av_valor == "FAILED":
                    tp += 1
                elif gt_valor == "PASSED" and av_valor == "FAILED":
                    fp += 1
                    linhas_discrepancias.append({
                        "Avaliador": rotulo, "Regra": regra, "ID do Caso": id_caso,
                        "Ground Truth": gt_valor, "Resultado Avaliador": av_valor,
                        "Tipo": "Falso Positivo (avaliador reprovou indevidamente)",
                    })
                elif gt_valor == "FAILED" and av_valor == "PASSED":
                    fn += 1
                    linhas_discrepancias.append({
                        "Avaliador": rotulo, "Regra": regra, "ID do Caso": id_caso,
                        "Ground Truth": gt_valor, "Resultado Avaliador": av_valor,
                        "Tipo": "Falso Negativo (avaliador aprovou indevidamente)",
                    })
                elif gt_valor == "PASSED" and av_valor == "PASSED":
                    tn += 1

            precision, recall, f1, accuracy = calcular_metricas(tp, fp, fn, tn)
            linhas_metricas.append({
                "Avaliador": rotulo, "Regra": regra,
                "TP": tp, "FP": fp, "FN": fn, "TN": tn,
                "Divergencias N/A": na_mismatches,
                "Precision": fmt(precision), "Recall": fmt(recall),
                "F1": fmt(f1), "Accuracy": fmt(accuracy),
            })

        # linha agregada (micro-media) somando TP/FP/FN/TN de todas as regras
        tp_tot = sum(l["TP"] for l in linhas_metricas if l["Avaliador"] == rotulo)
        fp_tot = sum(l["FP"] for l in linhas_metricas if l["Avaliador"] == rotulo)
        fn_tot = sum(l["FN"] for l in linhas_metricas if l["Avaliador"] == rotulo)
        tn_tot = sum(l["TN"] for l in linhas_metricas if l["Avaliador"] == rotulo)
        precision, recall, f1, accuracy = calcular_metricas(tp_tot, fp_tot, fn_tot, tn_tot)
        linhas_metricas.append({
            "Avaliador": rotulo, "Regra": "TODAS (micro-media)",
            "TP": tp_tot, "FP": fp_tot, "FN": fn_tot, "TN": tn_tot,
            "Divergencias N/A": sum(l["Divergencias N/A"] for l in linhas_metricas if l["Avaliador"] == rotulo),
            "Precision": fmt(precision), "Recall": fmt(recall),
            "F1": fmt(f1), "Accuracy": fmt(accuracy),
        })

    colunas_metricas = ["Avaliador", "Regra", "TP", "FP", "FN", "TN", "Divergencias N/A",
                        "Precision", "Recall", "F1", "Accuracy"]
    with (ANALISES_DIR / "metricas_por_regra.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_metricas, delimiter=";")
        w.writeheader()
        w.writerows(linhas_metricas)

    colunas_disc = ["Avaliador", "Regra", "ID do Caso", "Ground Truth", "Resultado Avaliador", "Tipo"]
    with (ANALISES_DIR / "discrepancias_por_regra.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_disc, delimiter=";")
        w.writeheader()
        w.writerows(linhas_discrepancias)

    print(f"OK: metricas por regra salvas em {ANALISES_DIR / 'metricas_por_regra.csv'}")
    print(f"OK: {len(linhas_discrepancias)} discrepancias detalhadas em {ANALISES_DIR / 'discrepancias_por_regra.csv'}")


if __name__ == "__main__":
    main()
