#!/usr/bin/env python3
"""
Segundo passo da preparacao da revisao humana: le o gabarito privado de CADA
avaliador (privada/revisores/<codigo>/mapa_ids.csv) e os planos renderizados
em texto (gerados pelo common/sadcloud/scripts/run_show_all.sh via
`terraform show`), e monta a pasta publica/<codigo>/planos daquele avaliador
com nomes puramente numericos (plano_01.txt .. plano_NN.txt), sem nenhuma
referencia ao nome original do arquivo ou ao status de conformidade.

Ajuste (ponto 8 da resposta do orientador, 2026-08-31): como cada avaliador
agora tem seu proprio embaralhamento (ver gerar_mapa_ids.py), este script
gera uma pasta publica/<codigo>/planos SEPARADA por avaliador - o mesmo
conteudo de 30 planos, mas com uma correspondencia plano_NN -> caso
diferente para cada avaliador.

Script comum: opera sobre QUALQUER conjunto (training_set ou test_set),
indicado como argumento de linha de comando.

Uso:
    python3 finalizar_planos_publicos.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/revisao_humana/):
    python3 finalizar_planos_publicos.py ../../training_set
    python3 finalizar_planos_publicos.py ../../test_set

Rode este script SOMENTE depois de:
  1) ja ter rodado o gerar_mapa_ids.py deste set (gabaritos por avaliador existentes)
  2) ja ter rodado o run_plans.sh (ou equivalente) do set (planos .plan existentes)
  3) ja ter rodado o run_show_all.sh do set (textos .txt existentes em
     <set>/sadcloud/tfvars/human_review_raw/)
"""
import csv
import re
import sys
from pathlib import Path

# Deve ser a MESMA lista usada em gerar_mapa_ids.py.
REVISORES = ["R1", "R2", "R3"]

# strings que NUNCA podem aparecer no material publico (checagem de seguranca)
PADROES_PROIBIDOS = re.compile(r"noncompliant|compliant", re.IGNORECASE)


def processar_revisor(codigo: str, SET_ROOT: Path, RAW_DIR: Path):
    PRIVADA = SET_ROOT / "revisao_humana" / "privada"
    PUBLICA = SET_ROOT / "revisao_humana" / "publica"
    MAPA_CSV = PRIVADA / "revisores" / codigo / "mapa_ids.csv"
    DEST_DIR = PUBLICA / codigo / "planos"

    if not MAPA_CSV.exists():
        print(f"[{codigo}] PULADO: {MAPA_CSV} nao existe. Rode gerar_mapa_ids.py primeiro para este set.")
        return [], 0

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
                avisos.append(f"[{codigo}][FALTANDO] {origem} nao existe - pulei plano_{id_publico}")
                continue

            conteudo = origem.read_text(encoding="utf-8", errors="replace")

            if PADROES_PROIBIDOS.search(conteudo):
                avisos.append(
                    f"[{codigo}][ATENCAO] plano_{id_publico} ({arquivo_original}) contem a string "
                    "'compliant'/'noncompliant' no texto renderizado - REVISE ANTES DE ENVIAR!"
                )

            destino.write_text(conteudo, encoding="utf-8")
            total += 1

    print(f"[{codigo}] OK: {total} planos copiados para {DEST_DIR}")
    return avisos, total


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 finalizar_planos_publicos.py <caminho_para_o_set>\n"
            "Exemplos: python3 finalizar_planos_publicos.py ../../training_set\n"
            "          python3 finalizar_planos_publicos.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    RAW_DIR = SET_ROOT / "sadcloud" / "tfvars" / "human_review_raw"

    if not RAW_DIR.exists():
        raise SystemExit(
            f"Nao encontrei {RAW_DIR}.\n"
            "Rode antes, no host com Docker (dentro de common/sadcloud/sadcloud):\n"
            '  TFVARS_DIR=<caminho_do_set>/sadcloud/tfvars docker compose run --rm '
            '--entrypoint sh terraform -c "sh /scripts/run_show_all.sh"'
        )

    todos_avisos = []
    total_geral = 0
    for codigo in REVISORES:
        avisos, total = processar_revisor(codigo, SET_ROOT, RAW_DIR)
        todos_avisos.extend(avisos)
        total_geral += total

    if todos_avisos:
        print("\n--- AVISOS ---")
        for a in todos_avisos:
            print(a)
        sys.exit(1 if any("[ATENCAO]" in a for a in todos_avisos) else 0)

    print(f"\nOK geral: {total_geral} planos copiados no total, entre {len(REVISORES)} avaliadores.")


if __name__ == "__main__":
    main()
