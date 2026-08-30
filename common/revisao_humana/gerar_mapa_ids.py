#!/usr/bin/env python3
"""
Gera o mapeamento privado ID publico (1..N) <-> caso original, com ordem
embaralhada (para nao correlacionar o numero do ID com conformidade,
complexidade ou posicao original).

Script comum: opera sobre QUALQUER conjunto (training_set ou test_set),
indicado como argumento de linha de comando.

Uso:
    python3 gerar_mapa_ids.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/revisao_humana/):
    python3 gerar_mapa_ids.py ../../training_set
    python3 gerar_mapa_ids.py ../../test_set

Le a caracterizacao dos casos em <set>/analises/amostras.md (fonte unica de
verdade) e escreve:
  - <set>/revisao_humana/privada/mapa_ids.csv  (gabarito - NUNCA vai para o zip publico)
  - o esqueleto de pastas de <set>/revisao_humana/publica e /privada

Reprodutibilidade: usa uma seed fixa (RANDOM_SEED) para que o embaralhamento
possa ser regerado de forma identica se necessario. Se o dataset tiver um
numero de casos diferente de 30 (ex.: os 15 pares = 30 planos do test_set),
o script funciona igual - so avisa se nao achar nenhuma linha valida.
"""
import csv
import random
import re
import sys
from pathlib import Path

RANDOM_SEED = 20260826  # fixo para reprodutibilidade


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
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 gerar_mapa_ids.py <caminho_para_o_set>\n"
            "Exemplos: python3 gerar_mapa_ids.py ../../training_set\n"
            "          python3 gerar_mapa_ids.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    AMOSTRAS_MD = SET_ROOT / "analises" / "amostras.md"
    PRIVADA = SET_ROOT / "revisao_humana" / "privada"
    PUBLICA = SET_ROOT / "revisao_humana" / "publica"
    MAPA_CSV = PRIVADA / "mapa_ids.csv"

    if not AMOSTRAS_MD.exists():
        raise SystemExit(f"Nao encontrei {AMOSTRAS_MD}")

    casos = parse_amostras(AMOSTRAS_MD)
    if not casos:
        raise SystemExit(f"Nao encontrei nenhuma linha valida em {AMOSTRAS_MD}. Confira o formato da tabela.")

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

    # embaralha com seed fixa e distribui IDs publicos 1..N
    random.seed(RANDOM_SEED)
    ordem = casos[:]
    random.shuffle(ordem)
    largura = len(str(len(ordem)))
    for i, c in enumerate(ordem, start=1):
        c["id_publico"] = str(i).zfill(max(2, largura))

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

    print(f"OK: {len(ordem)} casos mapeados (seed={RANDOM_SEED}) para o set em {SET_ROOT}")
    print(f"Gabarito privado salvo em: {MAPA_CSV}")
    print(f"Pasta publica preparada em: {PUBLICA}")


if __name__ == "__main__":
    main()
