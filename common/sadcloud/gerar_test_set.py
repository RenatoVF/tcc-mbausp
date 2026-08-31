#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera os 180 planos (.tfvars) do test_set (90 pares conforme/nao-conforme),
conforme o desenho documentado no README.md (secao 6): 75 pares de violacao
unica (5 regras x 3 complexidades x 5 repeticoes) + 15 pares de violacao
multipla (5 por complexidade, combinacoes nao-contraditorias de 2-3 regras).

Uso: python3 gerar_test_set.py <diretorio_saida>
"""
import os
import sys
import random
import textwrap

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "./test_set/sadcloud/tfvars"
os.makedirs(SAIDA, exist_ok=True)

SEED = 20260831  # data da geracao, fixa e documentada
rng = random.Random(SEED)

REGRAS = ["01", "02", "03", "04A", "04B"]
COMPLEXIDADES = ["simple", "medium", "complex"]

REGIOES_ERRADAS = ["us-west-2", "eu-west-1", "ap-southeast-1", "sa-east-1", "eu-central-1"]
AMBIENTES_INVALIDOS = ["DEV", "STG", "QA", "producao", "homolog"]
# NOTA: "Ambiente" foi removida desta rotacao apos o script de verificacao
# do ground truth (common/analises/gerar_ground_truth.py) apontar que
# esvaziar a tag "Ambiente" para violar a regra 01 (tags obrigatorias) tambem
# viola, como efeito colateral inevitavel, a regra 02 (valores validos de
# "Ambiente" - string vazia nao e 'PRD' nem 'HML'), contaminando os casos de
# violacao unica da regra 01. "Projeto" e "Time Responsavel" nao tem esse
# problema (nenhuma outra regra depende do valor dessas tags).
TAGS_ROTACAO_01 = ["Projeto", "Time Responsável"]

registros = []  # linhas para a tabela de mapeamento (amostras.md do test_set)


def fmt_tags(tags):
    linhas = ["required_tags = {"]
    for k, v in tags.items():
        if " " in k or k not in ("Projeto", "Ambiente"):
            linhas.append(f'  "{k}" = "{v}"')
        else:
            linhas.append(f'  {k} = "{v}"')
    linhas.append("}")
    return "\n".join(linhas)


def escrever_tfvars(nome, comentario, aws_region, tags, extras):
    caminho = os.path.join(SAIDA, f"{nome}.tfvars")
    partes = []
    if comentario:
        partes.append(f"# {comentario}")
    partes.append(f'aws_region = "{aws_region}"')
    partes.append(fmt_tags(tags))
    partes.append("")
    for linha in extras:
        partes.append(linha)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(partes) + "\n")


def base_tags(ambiente, time_label):
    return {"Projeto": "TCC", "Time Responsável": time_label, "Ambiente": ambiente}


# ---------------------------------------------------------------------------
# Perfis de recurso por complexidade
# ---------------------------------------------------------------------------

def extras_simple(tipo_recurso, instance_type="t2.micro", rds_class="db.t2.micro"):
    linhas = ["enable_network = true"]
    ec2 = rds = s3 = False
    if tipo_recurso in ("ec2", "ec2+rds"):
        ec2 = True
    if tipo_recurso in ("rds", "ec2+rds"):
        rds = True
    if tipo_recurso == "s3":
        s3 = True
    linhas.append(f"enable_ec2 = {'true' if ec2 else 'false'}")
    linhas.append(f"enable_rds = {'true' if rds else 'false'}")
    linhas.append(f"enable_s3 = {'true' if s3 else 'false'}")
    if ec2:
        linhas.append("ec2_count = 1")
        linhas.append(f'instance_type = "{instance_type}"')
    if rds:
        linhas.append("rds_count = 1")
        linhas.append(f'rds_instance_class = "{rds_class}"')
    return linhas


def extras_medium(rep, instance_type="t2.small", rds_class="db.t2.micro"):
    perfis = [(2, 1, False), (3, 1, False), (2, 2, False), (3, 2, True), (2, 1, True)]
    ec2c, rdsc, elbv2 = perfis[(rep - 1) % len(perfis)]
    linhas = [
        "enable_network = true",
        "enable_ec2 = true",
        "enable_rds = true",
        "enable_s3 = true",
        f"enable_elbv2 = {'true' if elbv2 else 'false'}",
        f"ec2_count = {ec2c}",
        f"rds_count = {rdsc}",
        f'instance_type = "{instance_type}"',
        f'rds_instance_class = "{rds_class}"',
    ]
    return linhas, ec2c, rdsc


def extras_complex(rep, instance_type="t2.small", rds_class="db.t2.micro"):
    ec2_opts = [4, 5, 6, 7, 8]
    rds_opts = [2, 2, 3, 3, 2]
    ec2c = ec2_opts[(rep - 1) % len(ec2_opts)]
    rdsc = rds_opts[(rep - 1) % len(rds_opts)]
    linhas = [
        "enable_network = true",
        "enable_ec2 = true",
        "enable_rds = true",
        "enable_s3 = true",
        "enable_elbv2 = true",
        "enable_eks = true",
        f"ec2_count = {ec2c}",
        f"rds_count = {rdsc}",
        f'instance_type = "{instance_type}"',
        f'rds_instance_class = "{rds_class}"',
    ]
    return linhas, ec2c, rdsc


# ---------------------------------------------------------------------------
# 1) 75 pares de violacao unica
# ---------------------------------------------------------------------------

# 15 slots (5 reps x 3 complexidades) distribuidos entre as 2 tags validas
# (8+7) - mesmo tamanho de lista (15) que antes, para nao alterar a posicao
# do gerador de numeros aleatorios usado pelas demais decisoes do script.
rotacao_tag01 = [TAGS_ROTACAO_01[i % len(TAGS_ROTACAO_01)] for i in range(15)]
rng.shuffle(rotacao_tag01)
idx_tag01 = 0

recurso_rotacao_simple = ["ec2", "rds", "s3", "ec2", "rds"]

contador_time = 1

for complexidade in COMPLEXIDADES:
    for regra in REGRAS:
        for rep in range(1, 6):
            time_label = f"Time {contador_time:02d}"
            contador_time += 1
            nome_base = f"{complexidade}-{regra.lower()}-{rep:02d}"
            comentario_extra = ""

            if regra == "04A":
                ambiente = "HML"
            elif regra == "04B":
                ambiente = "HML"
            else:
                ambiente = "PRD"

            tags_compliant = base_tags(ambiente, time_label)
            tags_noncompliant = dict(tags_compliant)

            regiao_compliant = "us-east-1"
            regiao_noncompliant = "us-east-1"

            it_compliant = "t2.micro"
            it_noncompliant = "t2.micro"
            rc_compliant = "db.t2.micro"
            rc_noncompliant = "db.t2.micro"

            if regra == "01":
                subtipo = rotacao_tag01[idx_tag01]
                idx_tag01 += 1
                tags_noncompliant[subtipo] = ""
                comentario_extra = f"violacao = tag '{subtipo}' vazia"
            elif regra == "02":
                valor_invalido = AMBIENTES_INVALIDOS[(rep - 1) % len(AMBIENTES_INVALIDOS)]
                tags_noncompliant["Ambiente"] = valor_invalido
                comentario_extra = f"violacao = Ambiente invalido ('{valor_invalido}')"
            elif regra == "03":
                regiao_noncompliant = REGIOES_ERRADAS[(rep - 1) % len(REGIOES_ERRADAS)]
                comentario_extra = f"violacao = regiao ({regiao_noncompliant})"
            elif regra == "04A":
                it_noncompliant = "m5.large"
                comentario_extra = "violacao = EC2 fora da familia 't' em HML"
            elif regra == "04B":
                rc_noncompliant = "db.m5.large"
                comentario_extra = "violacao = RDS fora da familia 'db.t' em HML"

            if complexidade == "simple":
                if regra == "04A":
                    tipo_recurso = "ec2"
                elif regra == "04B":
                    tipo_recurso = "rds"
                else:
                    tipo_recurso = recurso_rotacao_simple[(rep - 1) % len(recurso_rotacao_simple)]
                extras_c = extras_simple(tipo_recurso, it_compliant, rc_compliant)
                extras_nc = extras_simple(tipo_recurso, it_noncompliant, rc_noncompliant)
                recursos_desc = {"ec2": "EC2(1)", "rds": "RDS(1)", "s3": "S3"}[tipo_recurso]
            elif complexidade == "medium":
                extras_c, ec2c, rdsc = extras_medium(rep, it_compliant, rc_compliant)
                extras_nc, _, _ = extras_medium(rep, it_noncompliant, rc_noncompliant)
                recursos_desc = f"EC2({ec2c}), RDS({rdsc}), S3"
            else:
                extras_c, ec2c, rdsc = extras_complex(rep, it_compliant, rc_compliant)
                extras_nc, _, _ = extras_complex(rep, it_noncompliant, rc_noncompliant)
                recursos_desc = f"EC2({ec2c}), RDS({rdsc}), S3, ELBv2, EKS"

            nome_c = f"compliant-{nome_base}"
            nome_nc = f"noncompliant-{nome_base}"

            escrever_tfvars(nome_c, "", regiao_compliant, tags_compliant, extras_c)
            escrever_tfvars(
                nome_nc,
                f"Par de {nome_c}: {comentario_extra}",
                regiao_noncompliant,
                tags_noncompliant,
                extras_nc,
            )

            registros.append({
                "tipo": "unica",
                "complexidade": complexidade,
                "regras": regra,
                "rep": rep,
                "arquivo_c": nome_c,
                "arquivo_nc": nome_nc,
                "recursos": recursos_desc,
                "violacao": comentario_extra,
            })

print(f"[OK] {len(registros)} pares de violacao unica gerados ({len(registros)*2} arquivos).")

# ---------------------------------------------------------------------------
# 2) 15 pares de violacao multipla (combinacoes nao-contraditorias)
#
# CKV_FINOPS_02 (Ambiente invalido) e CKV_FINOPS_04A/04B (exigem Ambiente ==
# 'HML') sao mutuamente exclusivas - a tag Ambiente so pode ter um valor.
# Por isso, das 20 combinacoes possiveis de 2-3 regras entre as 5, apenas 13
# sao logicamente possiveis (excluidas as que combinam 02 com 04A e/ou 04B).
# ---------------------------------------------------------------------------

COMBOS_VALIDAS = [
    ("01", "02"), ("01", "03"), ("01", "04A"), ("01", "04B"), ("02", "03"),
    ("03", "04A"), ("03", "04B"), ("04A", "04B"),
    ("01", "02", "03"), ("01", "03", "04A"), ("01", "03", "04B"),
    ("01", "04A", "04B"), ("03", "04A", "04B"),
]

COMBOS_POR_COMPLEXIDADE = {
    "simple": [COMBOS_VALIDAS[0], COMBOS_VALIDAS[1], COMBOS_VALIDAS[2], COMBOS_VALIDAS[3], COMBOS_VALIDAS[4]],
    "medium": [COMBOS_VALIDAS[5], COMBOS_VALIDAS[6], COMBOS_VALIDAS[7], COMBOS_VALIDAS[8], COMBOS_VALIDAS[9]],
    # complex reaproveita COMBOS_VALIDAS[0] ("01","02") e COMBOS_VALIDAS[5] ("03","04A"),
    # ja usadas em simple/medium - unicas repeticoes do desenho, documentadas no README.
    "complex": [COMBOS_VALIDAS[10], COMBOS_VALIDAS[11], COMBOS_VALIDAS[12], COMBOS_VALIDAS[0], COMBOS_VALIDAS[5]],
}

registros_multi = []

for complexidade in COMPLEXIDADES:
    combos = COMBOS_POR_COMPLEXIDADE[complexidade]
    for rep, combo in enumerate(combos, start=1):
        time_label = f"Time {contador_time:02d}"
        contador_time += 1
        precisa_04a = "04A" in combo
        precisa_04b = "04B" in combo
        ambiente_base = "HML" if (precisa_04a or precisa_04b) else "PRD"

        tags_compliant = base_tags(ambiente_base, time_label)
        tags_noncompliant = dict(tags_compliant)

        regiao_compliant = "us-east-1"
        regiao_noncompliant = "us-east-1"
        it_compliant, it_noncompliant = "t2.micro", "t2.micro"
        rc_compliant, rc_noncompliant = "db.t2.micro", "db.t2.micro"

        descricoes = []
        if "01" in combo:
            tags_noncompliant["Projeto"] = ""
            descricoes.append("tag 'Projeto' vazia")
        if "02" in combo:
            valor_invalido = AMBIENTES_INVALIDOS[rep % len(AMBIENTES_INVALIDOS)]
            tags_noncompliant["Ambiente"] = valor_invalido
            descricoes.append(f"Ambiente invalido ('{valor_invalido}')")
        if "03" in combo:
            regiao_noncompliant = REGIOES_ERRADAS[rep % len(REGIOES_ERRADAS)]
            descricoes.append(f"regiao ({regiao_noncompliant})")
        if precisa_04a:
            it_noncompliant = "m5.large"
            descricoes.append("EC2 fora da familia 't' em HML")
        if precisa_04b:
            rc_noncompliant = "db.m5.large"
            descricoes.append("RDS fora da familia 'db.t' em HML")

        nome_base = f"{complexidade}-multi-{rep:02d}"
        nome_c = f"compliant-{nome_base}"
        nome_nc = f"noncompliant-{nome_base}"

        if complexidade == "simple":
            if precisa_04a and precisa_04b:
                tipo_recurso = "ec2+rds"
            elif precisa_04a:
                tipo_recurso = "ec2"
            elif precisa_04b:
                tipo_recurso = "rds"
            else:
                tipo_recurso = "ec2"
            extras_c = extras_simple(tipo_recurso, it_compliant, rc_compliant)
            extras_nc = extras_simple(tipo_recurso, it_noncompliant, rc_noncompliant)
            recursos_desc = {"ec2": "EC2(1)", "rds": "RDS(1)", "ec2+rds": "EC2(1), RDS(1)"}[tipo_recurso]
        elif complexidade == "medium":
            extras_c, ec2c, rdsc = extras_medium(rep, it_compliant, rc_compliant)
            extras_nc, _, _ = extras_medium(rep, it_noncompliant, rc_noncompliant)
            recursos_desc = f"EC2({ec2c}), RDS({rdsc}), S3"
        else:
            extras_c, ec2c, rdsc = extras_complex(rep, it_compliant, rc_compliant)
            extras_nc, _, _ = extras_complex(rep, it_noncompliant, rc_noncompliant)
            recursos_desc = f"EC2({ec2c}), RDS({rdsc}), S3, ELBv2, EKS"

        comentario = f"Par de {nome_c}: violacao multipla ({', '.join(combo)}) - " + "; ".join(descricoes)

        escrever_tfvars(nome_c, "", regiao_compliant, tags_compliant, extras_c)
        escrever_tfvars(nome_nc, comentario, regiao_noncompliant, tags_noncompliant, extras_nc)

        registros_multi.append({
            "tipo": "multipla",
            "complexidade": complexidade,
            "regras": "+".join(combo),
            "rep": rep,
            "arquivo_c": nome_c,
            "arquivo_nc": nome_nc,
            "recursos": recursos_desc,
            "violacao": "; ".join(descricoes),
        })

print(f"[OK] {len(registros_multi)} pares de violacao multipla gerados ({len(registros_multi)*2} arquivos).")

todos_registros = registros + registros_multi
print(f"[TOTAL] {len(todos_registros)} pares / {len(todos_registros)*2} arquivos .tfvars em {SAIDA}")

# ---------------------------------------------------------------------------
# 3) Tabela de mapeamento (equivalente a training_set/analises/amostras.md)
# ---------------------------------------------------------------------------

CAMINHO_AMOSTRAS = os.path.join(os.path.dirname(SAIDA.rstrip("/")), "..", "analises", "amostras.md")
CAMINHO_AMOSTRAS = os.path.normpath(CAMINHO_AMOSTRAS)

linhas_md = [
    "# Mapeamento dos 180 casos do test_set (90 pares)\n",
    "Gerado por `common/sadcloud/gerar_test_set.py`, seed fixa "
    f"`{SEED}` (documentada no cabecalho do script, para reprodutibilidade).\n",
    "| Arquivo Compliant | Arquivo Non-compliant | Complexidade | Regra(s) Violada(s) | Recursos | Violacao |",
    "|---|---|---|---|---|---|",
]
for r in todos_registros:
    linhas_md.append(
        f"| {r['arquivo_c']} | {r['arquivo_nc']} | {r['complexidade']} | {r['regras']} | {r['recursos']} | {r['violacao']} |"
    )

os.makedirs(os.path.dirname(CAMINHO_AMOSTRAS), exist_ok=True)
with open(CAMINHO_AMOSTRAS, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_md) + "\n")

print(f"[OK] Tabela de mapeamento salva em {CAMINHO_AMOSTRAS}")

# ---------------------------------------------------------------------------
# 4) Selecao estratificada dos 15 pares (30 planos) para revisao humana
# ---------------------------------------------------------------------------

rng_selecao = random.Random(SEED + 1)  # seed derivada, tambem fixa e documentada

selecionados = []
for complexidade in COMPLEXIDADES:
    unicos_desta_complexidade = [r for r in registros if r["complexidade"] == complexidade]
    # 1 pair por regra, priorizando cobrir as 5 regras - mas so pegamos 4,
    # entao sorteamos (com seed) 4 das 5 regras, e dentro de cada uma,
    # sorteamos 1 das 5 repeticoes disponiveis.
    regras_disponiveis = REGRAS[:]
    rng_selecao.shuffle(regras_disponiveis)
    regras_escolhidas = regras_disponiveis[:4]
    for regra in regras_escolhidas:
        candidatos = [r for r in unicos_desta_complexidade if r["regras"] == regra]
        escolhido = rng_selecao.choice(candidatos)
        selecionados.append(escolhido)

    multi_desta_complexidade = [r for r in registros_multi if r["complexidade"] == complexidade]
    escolhido_multi = rng_selecao.choice(multi_desta_complexidade)
    selecionados.append(escolhido_multi)

CAMINHO_SELECAO = os.path.normpath(os.path.join(os.path.dirname(CAMINHO_AMOSTRAS), "selecao_revisao_humana.md"))
linhas_sel = [
    "# Selecao estratificada para revisao humana (test_set)\n",
    f"Amostragem estratificada com seed fixa `{SEED + 1}` (derivada da seed de geracao dos planos, "
    f"`{SEED}`, documentada em `gerar_test_set.py`): 5 pares por nivel de complexidade, sendo em cada "
    "nivel 4 pares de violacao unica (sorteados entre as regras, priorizando cobertura) e 1 par de "
    "violacao multipla. Total: 15 pares (30 planos).\n",
    "| Arquivo Compliant | Arquivo Non-compliant | Complexidade | Regra(s) | Tipo |",
    "|---|---|---|---|---|",
]
for r in selecionados:
    tipo = "unica" if r["tipo"] == "unica" else "multipla"
    linhas_sel.append(f"| {r['arquivo_c']} | {r['arquivo_nc']} | {r['complexidade']} | {r['regras']} | {tipo} |")

with open(CAMINHO_SELECAO, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_sel) + "\n")

print(f"[OK] Selecao para revisao humana ({len(selecionados)} pares) salva em {CAMINHO_SELECAO}")
