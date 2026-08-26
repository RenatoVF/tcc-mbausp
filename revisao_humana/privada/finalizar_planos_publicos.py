#!/usr/bin/env python3
"""
Segundo passo da preparacao da revisao humana: le o gabarito privado
(mapa_ids.csv) e os planos renderizados em texto (gerados pelo
sadcloud/tfvars/run_show_all.sh via `terraform show`), e monta a pasta
publica/planos com nomes puramente numericos (plano_01.txt .. plano_30.txt),
sem nenhuma referencia ao nome original do arquivo ou ao status de
conformidade.

Rode este script SOMENTE depois de:
  1) ja ter rodado sadcloud/tfvars/run_plans.sh (planos .plan existentes)
  2) ja ter rodado o novo sadcloud/tfvars/run_show_all.sh (textos .txt existentes
     em sadcloud/tfvars/human_review_raw/)
"""
import csv
import re
import shutil
import sys
from pathlib import Path

PRIVADA = Path(__file__).resolve().parent          # .../revisao_humana/privada
RAIZ = PRIVADA.parents[1]                           # .../Dataset
PUBLICA = PRIVADA.parent / "publica"
MAPA_CSV = PRIVADA / "mapa_ids.csv"
RAW_DIR = RAIZ / "sadcloud" / "tfvars" / "human_review_raw"
DEST_DIR = PUBLICA / "planos"

# strings que NUNCA podem aparecer no material publico (checagem de seguranca)
PADROES_PROIBIDOS = re.compile(r"noncompliant|compliant", re.IGNORECASE)


def main():
    if not MAPA_CSV.exists():
        raise SystemExit(f"Nao encontrei {MAPA_CSV}. Rode gerar_mapa_ids.py primeiro.")
    if not RAW_DIR.exists():
        raise SystemExit(
            f"Nao encontrei {RAW_DIR}.\n"
            "Rode antes, no host com Docker (dentro de sadcloud/sadcloud):\n"
            '  docker compose run --rm --entrypoint sh terraform -c "../tfvars/run_show_all.sh"'
        )

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    avisos = []
    total = 0
    with MAPA_CSV.open(encoding="utf-8") as f:
        leitor = csv.DictReader(f, delimiter=";")
        for linha in leitor:
            id_publico = linha["id_publico"]
            arquivo_original = linha["arquivo_original"]
            origem = RAW_DIR / f"{arquivo_original}.txt"
            destino = DEST_DIR / f"plano_{id_publico}.txt"

            if not origem.exists():
                avisos.append(f"[FALTANDO] {origem} nao existe - pulei plano_{id_publico}")
                continue

            conteudo = origem.read_text(encoding="utf-8", errors="replace")

            if PADROES_PROIBIDOS.search(conteudo):
                avisos.append(
                    f"[ATENCAO] plano_{id_publico} ({arquivo_original}) contem a string "
                    "'compliant'/'noncompliant' no texto renderizado - REVISE ANTES DE ENVIAR!"
                )

            destino.write_text(conteudo, encoding="utf-8")
            total += 1

    print(f"OK: {total} planos copiados para {DEST_DIR}")
    if avisos:
        print("\n--- AVISOS ---")
        for a in avisos:
            print(a)
        sys.exit(1 if any(a.startswith("[ATENCAO]") for a in avisos) else 0)


if __name__ == "__main__":
    main()
