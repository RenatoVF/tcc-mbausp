#!/usr/bin/env python3
"""
Segundo passo da preparacao da revisao humana: le o gabarito privado
(mapa_ids.csv) e os planos renderizados em texto (gerados pelo
common/sadcloud/scripts/run_show_all.sh via `terraform show`), e monta a
pasta publica/planos do set indicado com nomes puramente numericos
(plano_01.txt .. plano_NN.txt), sem nenhuma referencia ao nome original do
arquivo ou ao status de conformidade.

Script comum: opera sobre QUALQUER conjunto (training_set ou test_set),
indicado como argumento de linha de comando.

Uso:
    python3 finalizar_planos_publicos.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/revisao_humana/):
    python3 finalizar_planos_publicos.py ../../training_set
    python3 finalizar_planos_publicos.py ../../test_set

Rode este script SOMENTE depois de:
  1) ja ter rodado o run_plans.sh (ou equivalente) do set (planos .plan existentes)
  2) ja ter rodado o run_show_all.sh do set (textos .txt existentes em
     <set>/sadcloud/tfvars/human_review_raw/)
"""
import csv
import re
import sys
from pathlib import Path

# strings que NUNCA podem aparecer no material publico (checagem de seguranca)
PADROES_PROIBIDOS = re.compile(r"noncompliant|compliant", re.IGNORECASE)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 finalizar_planos_publicos.py <caminho_para_o_set>\n"
            "Exemplos: python3 finalizar_planos_publicos.py ../../training_set\n"
            "          python3 finalizar_planos_publicos.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    PRIVADA = SET_ROOT / "revisao_humana" / "privada"
    PUBLICA = SET_ROOT / "revisao_humana" / "publica"
    MAPA_CSV = PRIVADA / "mapa_ids.csv"
    RAW_DIR = SET_ROOT / "sadcloud" / "tfvars" / "human_review_raw"
    DEST_DIR = PUBLICA / "planos"

    if not MAPA_CSV.exists():
        raise SystemExit(f"Nao encontrei {MAPA_CSV}. Rode gerar_mapa_ids.py primeiro para este set.")
    if not RAW_DIR.exists():
        raise SystemExit(
            f"Nao encontrei {RAW_DIR}.\n"
            "Rode antes, no host com Docker (dentro de common/sadcloud/sadcloud):\n"
            '  TFVARS_DIR=<caminho_do_set>/sadcloud/tfvars docker compose run --rm '
            '--entrypoint sh terraform -c "sh /scripts/run_show_all.sh"'
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
