#!/usr/bin/env python3
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys


def parse_total_monthly_cost(data):
    if isinstance(data, dict):
        if "totalMonthlyCost" in data:
            return data["totalMonthlyCost"]
        projects = data.get("projects")
        if isinstance(projects, list) and projects:
            project = projects[0]
            breakdown = project.get("breakdown")
            if isinstance(breakdown, dict) and "totalMonthlyCost" in breakdown:
                return breakdown["totalMonthlyCost"]
    return None


def format_currency(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return "N/A"
    return f"${amount.quantize(Decimal('0.01')):,.2f}"


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out")
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("infracost_summary.md")

    if not root.exists() or not root.is_dir():
        print(f"Erro: diretório não encontrado: {root}")
        sys.exit(1)

    files = sorted(root.glob("*.infracost.json"))
    if not files:
        print(f"Nenhum arquivo *.infracost.json encontrado em: {root}")
        sys.exit(1)

    rows = []
    for path in files:
        case_id = path.stem.replace(".infracost", "")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Aviso: erro ao ler {path}: {exc}")
            continue

        total = parse_total_monthly_cost(data)
        if total is None:
            formatted = "N/A"
        else:
            formatted = format_currency(total)
        rows.append((case_id, formatted))

    lines = [
        "# Infracost Summary",
        "",
        "> Cada caso usa a mesma referência de ID presente em `sadcloud/tfvars/plan_cases.md`.",
        "",
        "| Caso | Custo Mensal (USD) |",
        "|---|---:|",
    ]

    for case_id, cost in rows:
        lines.append(f"| {case_id} | {cost} |")

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Arquivo gerado: {output_file}")


if __name__ == "__main__":
    main()
