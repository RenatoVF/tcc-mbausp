#!/usr/bin/env python3
"""
Gera o mapeamento privado ID publico (1-30) <-> caso original, com ordem
embaralhada (para nao correlacionar o numero do ID com conformidade,
complexidade ou posicao original na pasta).

Le a caracterizacao dos 30 casos em analises/amostras.md (fonte unica de
verdade) e escreve:
  - revisao_humana/privada/mapa_ids.csv  (gabarito - NUNCA vai para o zip publico)
  - cria o esqueleto de pastas de revisao_humana/publica e revisao_humana/privada

Reprodutibilidade: usa uma seed fixa (RANDOM_SEED) para que o embaralhamento
possa ser regerado de forma identica se necessario.
"""
import csv
import random
import re
from pathlib import Path

RANDOM_SEED = 20260826  # fixo para reprodutibilidade (AAAAMMDD do dia da geracao)

RAIZ = Path(__file__).resolve().parents[2]  # .../Dataset
AMOSTRAS_MD = RAIZ / "analises" / "amostras.md"
PRIVADA = Path(__file__).resolve().parent   # .../revisao_humana/privada
PUBLICA = PRIVADA.parent / "publica"

MAPA_CSV = PRIVADA / "mapa_ids.csv"


def parse_amostras(md_path: Path):
    """Extrai as linhas da tabela markdown de analises/amostras.md."""
    casos = []
    linha_re = re.compile(
        r"^\|\s*(N?C\d{3})\s*\|\s*([\w-]+)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*$"
    )
    with md_path.open(encoding="utf-8") as f:
        for linha in f:
            m = linha_re.match(linha.strip())
            if not m:
                continue
            id_amostra, arquivo, complexidade, regra_violada, recursos, deps = m.groups()
            casos.append(
                {
                    "id_amostra_original": id_amostra,
                    "arquivo_original": arquivo,
                    "complexidade": complexidade,
                    "regra_violada": regra_violada,
                    "recursos_criados": recursos,
                }
            )
    return casos


def main():
    if not AMOSTRAS_MD.exists():
        raise SystemExit(f"Nao encontrei {AMOSTRAS_MD}")

    casos = parse_amostras(AMOSTRAS_MD)
    if len(casos) != 30:
        print(f"[AVISO] esperava 30 casos, encontrei {len(casos)}. Confira analises/amostras.md")

    for c in casos:
        eh_conforme = c["arquivo_original"].startswith("compliant-")
        eh_nao_conforme = c["arquivo_original"].startswith("noncompliant-")
        if not (eh_conforme or eh_nao_conforme):
            raise SystemExit(f"Nao consegui classificar conformidade de: {c['arquivo_original']}")
        c["conforme"] = "Sim" if eh_conforme else "Nao"

    # sanity check: regra_violada == 'Nenhuma' deve casar com conforme == Sim
    for c in casos:
        esperado = (c["regra_violada"].strip().lower() == "nenhuma")
        if esperado != (c["conforme"] == "Sim"):
            print(f"[AVISO] inconsistencia entre regra_violada e prefixo do arquivo em {c['arquivo_original']}")

    # embaralha com seed fixa e distribui IDs publicos 1..30
    random.seed(RANDOM_SEED)
    ordem = casos[:]
    random.shuffle(ordem)
    for i, c in enumerate(ordem, start=1):
        c["id_publico"] = f"{i:02d}"

    # reordena por ID publico soh para o CSV ficar legivel
    ordem.sort(key=lambda c: int(c["id_publico"]))

    PRIVADA.mkdir(parents=True, exist_ok=True)
    (PUBLICA / "planos").mkdir(parents=True, exist_ok=True)
    (PRIVADA / "revisores").mkdir(parents=True, exist_ok=True)

    colunas = [
        "id_publico",
        "arquivo_original",
        "id_amostra_original",
        "conforme",
        "complexidade",
        "regra_violada",
        "recursos_criados",
    ]
    with MAPA_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
        w.writeheader()
        for c in ordem:
            w.writerow({k: c[k] for k in colunas})

    print(f"OK: {len(ordem)} casos mapeados (seed={RANDOM_SEED}).")
    print(f"Gabarito privado salvo em: {MAPA_CSV}")
    print(f"Pasta publica preparada em: {PUBLICA}")


if __name__ == "__main__":
    main()
