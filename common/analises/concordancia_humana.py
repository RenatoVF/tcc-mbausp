#!/usr/bin/env python3
"""
Concordancia entre os 3 avaliadores humanos: mede o quanto R1/R2/R3
concordam entre si, indo alem da simples votacao majoritaria (que
sozinha nao caracteriza o grau de acordo real entre os avaliadores).

Calcula, por regra e agregado (pooled, tratando cada par caso/regra como um
"sujeito" independente):
  1. Concordancia percentual exata (proporcao de sujeitos em que os 3
     avaliadores deram exatamente a mesma resposta).
  2. Kappa de Fleiss, sobre as categorias efetivamente observadas
     (tipicamente PASSED/FAILED/N/A).

So entram no calculo os casos em que os 3 avaliadores (R1, R2, R3)
preencheram uma resposta valida para aquela regra (celula vazia ou nao
reconhecida, ja sinalizada como aviso por extrator_revisao_humana.py, e
excluida aqui e contada separadamente).

Uso:
    python3 concordancia_humana.py <caminho_para_o_set>

Gera:
    <set>/analises/concordancia_humana.csv
"""
import csv
import sys
from pathlib import Path

REGRAS = ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"]
REVISORES = ["R1", "R2", "R3"]

FAIXAS_LANDIS_KOCH = [
    (0.00, "Sem acordo (ou pior que o acaso)"),
    (0.20, "Leve"),
    (0.40, "Razoavel"),
    (0.60, "Moderado"),
    (0.80, "Substancial"),
    (1.01, "Quase perfeito"),
]


def interpretar_kappa(k):
    if k is None:
        return ""
    if k < 0:
        return FAIXAS_LANDIS_KOCH[0][1]
    for limite, rotulo in FAIXAS_LANDIS_KOCH[1:]:
        if k < limite:
            return rotulo
    return FAIXAS_LANDIS_KOCH[-1][1]


def ler_matriz_bruta(caminho):
    """Retorna dict {(id_caso, regra): {avaliador: valor}}."""
    dados = {}
    with caminho.open(encoding="utf-8") as f:
        leitor = csv.DictReader(f, delimiter=";")
        for linha in leitor:
            id_caso = linha["ID do Caso"]
            avaliador = linha["Avaliador"]
            for regra in REGRAS:
                valor = linha.get(regra, "")
                dados.setdefault((id_caso, regra), {})[avaliador] = valor
    return dados


def fleiss_kappa(matriz_contagem, categorias):
    """matriz_contagem: lista de dicts {categoria: contagem}, um por
    sujeito, com soma fixa n (numero de avaliadores) em cada um.
    Formula padrao de Fleiss (1971). Retorna None se so houver 1 sujeito
    ou 1 categoria observada (kappa indefinido/trivial)."""
    N = len(matriz_contagem)
    if N == 0:
        return None
    n = sum(matriz_contagem[0].get(c, 0) for c in categorias)
    if n < 2:
        return None

    p_j = {c: sum(sujeito.get(c, 0) for sujeito in matriz_contagem) / (N * n) for c in categorias}
    p_e = sum(p ** 2 for p in p_j.values())

    P_i = []
    for sujeito in matriz_contagem:
        soma_quadrados = sum(sujeito.get(c, 0) ** 2 for c in categorias)
        P_i.append((soma_quadrados - n) / (n * (n - 1)))
    p_bar = sum(P_i) / N

    if p_e >= 1.0:
        return None  # sem variabilidade possivel (uma unica categoria em todo o dataset)
    return (p_bar - p_e) / (1 - p_e)


def processar(dados_por_sujeito, sujeitos):
    """dados_por_sujeito: dict {sujeito: {avaliador: valor}} ja filtrado
    para os sujeitos de interesse. sujeitos: lista de chaves a considerar.
    Retorna (N_incluidos, N_excluidos, categorias_observadas,
    concordancia_pct, kappa)."""
    matriz_contagem = []
    excluidos = 0
    categorias_observadas = set()

    for s in sujeitos:
        respostas = dados_por_sujeito.get(s, {})
        valores = [respostas.get(r, "") for r in REVISORES]
        if any(v == "" for v in valores) or len(set(REVISORES) & set(respostas)) < 3:
            excluidos += 1
            continue
        for v in valores:
            categorias_observadas.add(v)
        contagem = {c: valores.count(c) for c in set(valores)}
        matriz_contagem.append(contagem)

    N_incluidos = len(matriz_contagem)
    if N_incluidos == 0:
        return 0, excluidos, categorias_observadas, None, None

    concordancia_exata = sum(1 for c in matriz_contagem if max(c.values()) == 3) / N_incluidos
    kappa = fleiss_kappa(matriz_contagem, sorted(categorias_observadas))
    return N_incluidos, excluidos, categorias_observadas, concordancia_exata, kappa


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 concordancia_humana.py <caminho_para_o_set>\n"
            "Exemplos: python3 concordancia_humana.py ../../training_set\n"
            "          python3 concordancia_humana.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    ANALISES_DIR = SET_ROOT / "analises"
    BRUTA_CSV = ANALISES_DIR / "matriz_resultados_humanos_bruta.csv"

    if not BRUTA_CSV.exists():
        raise SystemExit(
            f"Nao encontrei {BRUTA_CSV}. Rode extrator_revisao_humana.py "
            "(em common/revisao_humana/) primeiro para este set."
        )

    dados = ler_matriz_bruta(BRUTA_CSV)  # {(id_caso, regra): {avaliador: valor}}

    linhas = []
    todos_sujeitos_pool = list(dados.keys())

    for regra in REGRAS:
        sujeitos_regra = [k for k in dados if k[1] == regra]
        N, excluidos, cats, concordancia, kappa = processar(dados, sujeitos_regra)
        linhas.append({
            "Regra": regra,
            "N (casos incluidos)": N,
            "N (excluidos - dados incompletos)": excluidos,
            "Categorias observadas": ", ".join(sorted(cats)) if cats else "",
            "Concordancia exata (%)": "" if concordancia is None else f"{concordancia * 100:.1f}",
            "Fleiss Kappa": "" if kappa is None else f"{kappa:.3f}",
            "Interpretacao (Landis & Koch)": interpretar_kappa(kappa),
        })

    N, excluidos, cats, concordancia, kappa = processar(dados, todos_sujeitos_pool)
    linhas.append({
        "Regra": "TODAS (pooled - cada par caso/regra como um sujeito)",
        "N (casos incluidos)": N,
        "N (excluidos - dados incompletos)": excluidos,
        "Categorias observadas": ", ".join(sorted(cats)) if cats else "",
        "Concordancia exata (%)": "" if concordancia is None else f"{concordancia * 100:.1f}",
        "Fleiss Kappa": "" if kappa is None else f"{kappa:.3f}",
        "Interpretacao (Landis & Koch)": interpretar_kappa(kappa),
    })

    colunas = ["Regra", "N (casos incluidos)", "N (excluidos - dados incompletos)",
               "Categorias observadas", "Concordancia exata (%)", "Fleiss Kappa",
               "Interpretacao (Landis & Koch)"]
    with (ANALISES_DIR / "concordancia_humana.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
        w.writeheader()
        w.writerows(linhas)

    print(f"OK: concordancia entre avaliadores salva em {ANALISES_DIR / 'concordancia_humana.csv'}")


if __name__ == "__main__":
    main()
