#!/usr/bin/env python3
"""
Gera, para CADA avaliador humano (R1, R2, R3, ...), um mapeamento privado
INDEPENDENTE de ID publico (1..N) <-> caso original.

Cada avaliador deve receber uma ordem diferente dos planos, para reduzir
efeitos de aprendizado/fadiga e evitar que avaliadores comparem anotacoes
por numero de plano. Por isso este script gera um mapa_ids.csv por
avaliador (nao um unico arquivo compartilhado), cada um com seu proprio embaralhamento (seed
propria, derivada deterministicamente de SEED_BASE + indice do avaliador,
documentada abaixo para reprodutibilidade).

Script comum: opera sobre QUALQUER conjunto (training_set ou test_set),
indicado como argumento de linha de comando.

Uso:
    python3 gerar_mapa_ids.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/revisao_humana/):
    python3 gerar_mapa_ids.py ../../training_set
    python3 gerar_mapa_ids.py ../../test_set

Fonte dos casos (nesta ordem de preferencia):
  1. <set>/analises/selecao_revisao_humana.md - formato em PARES (usado pelo
     test_set: 15 pares = 30 planos selecionados para revisao humana dentre
     os 90 pares do holdout). Quando presente, os "Recursos" de cada par sao
     enriquecidos via join com <set>/analises/amostras.md (mesmo par de
     arquivos compliant/non-compliant).
  2. <set>/analises/amostras.md - formato em LINHA POR ARQUIVO (usado pelo
     training_set original: 30 casos, IDs C0xx/NC0xx). Mantido como fallback
     para nao quebrar o fluxo antigo.

Escreve, para cada avaliador em REVISORES:
  - <set>/revisao_humana/privada/revisores/<codigo>/mapa_ids.csv (gabarito
    daquele avaliador - NUNCA vai para o zip publico nem para o git, ver
    .gitignore)
  - o esqueleto de pastas <set>/revisao_humana/publica/<codigo>/planos

IMPORTANTE (privacidade/anonimato dos avaliadores, pedido explicito do
autor): este script e todo o pipeline de revisao humana identificam os
avaliadores SOMENTE pelos codigos R1/R2/R3 em qualquer artefato que possa
ir para o repositorio git. O nome real de cada avaliador (quando existir)
fica exclusivamente em <set>/revisao_humana/privada/mapa_revisores.csv, que
e a UNICA excecao versionada nessa pasta privada (como template vazio) -
qualquer preenchimento com nome real deve ser feito localmente e nunca
commitado (ver .gitignore).
"""
import csv
import random
import re
import sys
from pathlib import Path

# Seed base para o embaralhamento por avaliador. A seed real de cada
# avaliador e SEED_BASE + indice (0, 1, 2, ...) na lista REVISORES, para que
# o mapeamento de qualquer avaliador possa ser regerado de forma identica
# se necessario, sem precisar guardar N seeds soltas.
SEED_BASE = 20260826

# Codigos anonimos dos avaliadores. Ajuste esta lista se o numero de
# avaliadores mudar - o restante do script se adapta automaticamente.
REVISORES = ["R1", "R2", "R3"]


def parse_amostras_por_arquivo(md_path: Path):
    """Formato antigo (training_set): uma linha por arquivo, IDs C0xx/NC0xx."""
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


def parse_amostras_recursos_por_par(md_path: Path):
    """Le analises/amostras.md (formato em pares do test_set) e devolve um
    dict {(arquivo_compliant, arquivo_noncompliant): recursos} para
    enriquecer a selecao com a coluna 'Recursos'."""
    recursos_por_par = {}
    if not md_path.exists():
        return recursos_por_par
    linha_re = re.compile(
        r"^\|\s*([\w-]+)\s*\|\s*([\w-]+)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]*?)\s*\|\s*$"
    )
    with md_path.open(encoding="utf-8") as f:
        for linha in f:
            m = linha_re.match(linha.strip())
            if not m:
                continue
            compliant, noncompliant, _complexidade, _regras, recursos, _violacao = m.groups()
            if compliant.lower() in ("arquivo compliant",) or set(compliant) <= {"-", ":"}:
                continue
            recursos_por_par[(compliant, noncompliant)] = recursos
    return recursos_por_par


def parse_selecao_revisao_humana(md_path: Path, amostras_md_path: Path):
    """Formato novo (test_set): selecao_revisao_humana.md, em pares.
    Devolve uma lista com 2 casos (compliant + noncompliant) por par."""
    recursos_por_par = parse_amostras_recursos_por_par(amostras_md_path)

    casos = []
    linha_re = re.compile(
        r"^\|\s*([\w-]+)\s*\|\s*([\w-]+)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*$"
    )
    with md_path.open(encoding="utf-8") as f:
        for linha in f:
            m = linha_re.match(linha.strip())
            if not m:
                continue
            compliant, noncompliant, complexidade, regras, tipo = m.groups()
            if compliant.lower() in ("arquivo compliant",) or set(compliant) <= {"-", ":"}:
                continue
            recursos = recursos_por_par.get((compliant, noncompliant), "")
            par_id = f"{complexidade}-{regras}".replace(" ", "")
            casos.append(
                {
                    "id_amostra_original": f"C-{par_id}",
                    "arquivo_original": compliant,
                    "complexidade": complexidade,
                    "regra_violada": "Nenhuma",
                    "recursos_criados": recursos,
                    "tipo_selecao": tipo,
                }
            )
            casos.append(
                {
                    "id_amostra_original": f"NC-{par_id}",
                    "arquivo_original": noncompliant,
                    "complexidade": complexidade,
                    "regra_violada": regras,
                    "recursos_criados": recursos,
                    "tipo_selecao": tipo,
                }
            )
    return casos


def carregar_casos(set_root: Path):
    selecao_md = set_root / "analises" / "selecao_revisao_humana.md"
    amostras_md = set_root / "analises" / "amostras.md"

    if selecao_md.exists():
        print(f"Fonte: {selecao_md} (selecao em pares para revisao humana)")
        return parse_selecao_revisao_humana(selecao_md, amostras_md)

    if amostras_md.exists():
        print(f"Fonte: {amostras_md} (formato antigo, uma linha por arquivo)")
        return parse_amostras_por_arquivo(amostras_md)

    raise SystemExit(
        f"Nao encontrei nem {selecao_md} nem {amostras_md}. "
        "Nao ha fonte de casos para gerar o mapeamento."
    )


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 gerar_mapa_ids.py <caminho_para_o_set>\n"
            "Exemplos: python3 gerar_mapa_ids.py ../../training_set\n"
            "          python3 gerar_mapa_ids.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    PRIVADA = SET_ROOT / "revisao_humana" / "privada"
    PUBLICA = SET_ROOT / "revisao_humana" / "publica"

    casos = carregar_casos(SET_ROOT)
    if not casos:
        raise SystemExit("Nao encontrei nenhum caso valido. Confira o formato dos arquivos de origem.")

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

    colunas = [
        "id_publico",
        "arquivo_original",
        "id_amostra_original",
        "conforme",
        "complexidade",
        "regra_violada",
        "recursos_criados",
    ]

    (PUBLICA).mkdir(parents=True, exist_ok=True)
    (PRIVADA / "revisores").mkdir(parents=True, exist_ok=True)

    largura = len(str(len(casos)))

    for indice, codigo in enumerate(REVISORES):
        seed_revisor = SEED_BASE + indice
        random.seed(seed_revisor)
        ordem = casos[:]
        random.shuffle(ordem)
        for i, c in enumerate(ordem, start=1):
            c["id_publico"] = str(i).zfill(max(2, largura))
        ordem.sort(key=lambda c: int(c["id_publico"]))

        pasta_revisor_privada = PRIVADA / "revisores" / codigo
        pasta_revisor_privada.mkdir(parents=True, exist_ok=True)
        (PUBLICA / codigo / "planos").mkdir(parents=True, exist_ok=True)

        mapa_csv = pasta_revisor_privada / "mapa_ids.csv"
        with mapa_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
            w.writeheader()
            for c in ordem:
                w.writerow({k: c.get(k, "") for k in colunas})

        print(f"[{codigo}] seed={seed_revisor} -> {mapa_csv}")

    print()
    print(f"OK: {len(casos)} casos, {len(REVISORES)} avaliadores ({', '.join(REVISORES)}), cada um com ordem propria.")
    print(f"Gabaritos privados em: {PRIVADA / 'revisores' / '<codigo>' / 'mapa_ids.csv'}")
    print(f"Pastas publicas preparadas em: {PUBLICA / '<codigo>' / 'planos'}")


if __name__ == "__main__":
    main()
