#!/usr/bin/env python3
"""
Gera o ground truth (gabarito) por REGRA de FinOps, para cada caso de um
conjunto (training_set ou test_set), calculado de forma independente a
partir do plano JSON bruto do Terraform (nao usa Checkov nem LLM).

O veredito
final de um plano (Aprovado/Falhou) pode estar correto mesmo que um
avaliador erre uma regra especifica (ex.: um LLM que marca CKV_FINOPS_01
como Falhou num caso cuja unica anomalia injetada e um valor invalido em
CKV_FINOPS_02). Para medir isso, precisamos saber a resposta certa de
CADA regra, nao so do veredito agregado.

Uso:
    python3 gerar_ground_truth.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/analises/):
    python3 gerar_ground_truth.py ../../training_set
    python3 gerar_ground_truth.py ../../test_set

Le todos os *.json em <set>/sadcloud/tfvars/ e escreve
<set>/analises/ground_truth_regras.csv, no mesmo formato (colunas e
delimitador ';') de matriz_resultados_checkov.csv / matriz_resultados_llm.csv,
para facilitar o cruzamento posterior.

Regras implementadas (espelham a semantica das politicas em
common/checkov/rules/*.yaml, mas calculadas de forma independente):

- CKV_FINOPS_01: tags 'Projeto', 'Time Responsável' e 'Ambiente' devem
  existir e nao estar vazias em todo aws_instance/aws_db_instance/aws_s3_bucket
  criado ou atualizado no plano. N/A se nenhum recurso desses tipos existir.
- CKV_FINOPS_02: a tag 'Ambiente' (quando presente) deve valer 'PRD' ou
  'HML' em todo aws_instance/aws_db_instance/aws_s3_bucket. Mesmo escopo
  de aplicabilidade (N/A) de CKV_FINOPS_01.
- CKV_FINOPS_03: a regiao resolvida do provider AWS (direta ou via
  variavel) deve ser 'us-east-1'. N/A se o plano nao tiver nenhum recurso
  dos tipos cobertos pela regra.
- CKV_FINOPS_04A: se a tag 'Ambiente' de um aws_instance for 'HML', o
  instance_type deve comecar com 't'. N/A se nao houver nenhum
  aws_instance no plano.
- CKV_FINOPS_04B: se a tag 'Ambiente' de um aws_db_instance for 'HML', o
  instance_class deve comecar com 'db.t'. N/A se nao houver nenhum
  aws_db_instance no plano.

Unidade de analise: apenas resource_changes cujas acoes NAO sejam
exatamente ['delete'] ou ['no-op'] (mesmo recorte usado em
common/llm/avaliador_llm.py), para manter a mesma unidade experimental
entre os tres metodos.
"""
import csv
import json
import sys
from pathlib import Path

RECURSOS_TAGS = {"aws_instance", "aws_db_instance", "aws_s3_bucket"}
RECURSOS_REGIAO = {
    "aws_instance", "aws_db_instance", "aws_s3_bucket",
    "aws_elb", "aws_lb", "aws_eks_cluster",
}
AMBIENTES_VALIDOS = {"PRD", "HML"}


def resource_changes_validos(plano):
    """Filtra resource_changes ignorando acoes exatamente ['delete'] ou ['no-op']."""
    validos = []
    for res in plano.get("resource_changes", []):
        acoes = res.get("change", {}).get("actions", [])
        if acoes == ["delete"] or acoes == ["no-op"]:
            continue
        validos.append(res)
    return validos


def resolver_regiao(plano):
    """Resolve a regiao do provider AWS, direta ou via variavel."""
    provider_cfg = plano.get("configuration", {}).get("provider_config", {}).get("aws", {})
    expr = provider_cfg.get("expressions", {}).get("region", {})

    if "constant_value" in expr:
        return expr["constant_value"]

    referencias = expr.get("references", [])
    for ref in referencias:
        if ref.startswith("var."):
            nome_var = ref[len("var."):]
            var_info = plano.get("variables", {}).get(nome_var, {})
            if "value" in var_info:
                return var_info["value"]
    return None


def tag_nao_vazia(tags, chave):
    if not isinstance(tags, dict):
        return False
    valor = tags.get(chave)
    return isinstance(valor, str) and valor.strip() != ""


def avaliar_caso(plano):
    validos = resource_changes_validos(plano)
    regiao = resolver_regiao(plano)

    recursos_tags = [r for r in validos if r.get("type") in RECURSOS_TAGS]
    recursos_regiao = [r for r in validos if r.get("type") in RECURSOS_REGIAO]
    recursos_ec2 = [r for r in validos if r.get("type") == "aws_instance"]
    recursos_rds = [r for r in validos if r.get("type") == "aws_db_instance"]

    resultado = {}

    # CKV_FINOPS_01
    if not recursos_tags:
        resultado["CKV_FINOPS_01"] = "N/A"
    else:
        falhou = any(
            not (
                tag_nao_vazia(r.get("change", {}).get("after", {}).get("tags"), "Projeto")
                and tag_nao_vazia(r.get("change", {}).get("after", {}).get("tags"), "Time Responsável")
                and tag_nao_vazia(r.get("change", {}).get("after", {}).get("tags"), "Ambiente")
            )
            for r in recursos_tags
        )
        resultado["CKV_FINOPS_01"] = "FAILED" if falhou else "PASSED"

    # CKV_FINOPS_02
    if not recursos_tags:
        resultado["CKV_FINOPS_02"] = "N/A"
    else:
        def ambiente_valido(r):
            tags = r.get("change", {}).get("after", {}).get("tags") or {}
            return tags.get("Ambiente") in AMBIENTES_VALIDOS
        falhou = any(not ambiente_valido(r) for r in recursos_tags)
        resultado["CKV_FINOPS_02"] = "FAILED" if falhou else "PASSED"

    # CKV_FINOPS_03
    if not recursos_regiao:
        resultado["CKV_FINOPS_03"] = "N/A"
    else:
        resultado["CKV_FINOPS_03"] = "PASSED" if regiao == "us-east-1" else "FAILED"

    # CKV_FINOPS_04A
    if not recursos_ec2:
        resultado["CKV_FINOPS_04A"] = "N/A"
    else:
        def ec2_ok(r):
            after = r.get("change", {}).get("after", {})
            tags = after.get("tags") or {}
            if tags.get("Ambiente") != "HML":
                return True
            tipo = after.get("instance_type") or ""
            return tipo.startswith("t")
        falhou = any(not ec2_ok(r) for r in recursos_ec2)
        resultado["CKV_FINOPS_04A"] = "FAILED" if falhou else "PASSED"

    # CKV_FINOPS_04B
    if not recursos_rds:
        resultado["CKV_FINOPS_04B"] = "N/A"
    else:
        def rds_ok(r):
            after = r.get("change", {}).get("after", {})
            tags = after.get("tags") or {}
            if tags.get("Ambiente") != "HML":
                return True
            classe = after.get("instance_class") or ""
            return classe.startswith("db.t")
        falhou = any(not rds_ok(r) for r in recursos_rds)
        resultado["CKV_FINOPS_04B"] = "FAILED" if falhou else "PASSED"

    resultado["Veredito Ground Truth"] = (
        "FAILED" if "FAILED" in (resultado[r] for r in
            ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"])
        else "PASSED"
    )
    return resultado


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 gerar_ground_truth.py <caminho_para_o_set>\n"
            "Exemplos: python3 gerar_ground_truth.py ../../training_set\n"
            "          python3 gerar_ground_truth.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    TFVARS_DIR = SET_ROOT / "sadcloud" / "tfvars"
    ANALISES_DIR = SET_ROOT / "analises"
    SAIDA = ANALISES_DIR / "ground_truth_regras.csv"

    if not TFVARS_DIR.exists():
        raise SystemExit(f"Nao encontrei {TFVARS_DIR}")

    ANALISES_DIR.mkdir(parents=True, exist_ok=True)

    colunas = ["ID do Caso", "CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03",
               "CKV_FINOPS_04A", "CKV_FINOPS_04B", "Veredito Ground Truth"]

    linhas = []
    for arquivo in sorted(TFVARS_DIR.glob("*.json")):
        with arquivo.open(encoding="utf-8") as f:
            plano = json.load(f)
        resultado = avaliar_caso(plano)
        resultado["ID do Caso"] = arquivo.stem
        linhas.append(resultado)

    if not linhas:
        raise SystemExit(f"Nenhum plano .json encontrado em {TFVARS_DIR}")

    with SAIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
        w.writeheader()
        for linha in linhas:
            w.writerow({k: linha[k] for k in colunas})

    print(f"OK: {len(linhas)} casos avaliados. Ground truth salvo em: {SAIDA}")


if __name__ == "__main__":
    main()
