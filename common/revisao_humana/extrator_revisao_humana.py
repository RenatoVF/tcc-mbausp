#!/usr/bin/env python3
"""
Le os formularios de avaliacao (Formulario_Revisao_FinOps.docx) preenchidos
pelos 3 avaliadores humanos, cruza cada um com o mapa_ids.csv daquele
avaliador para recuperar o arquivo original de cada plano, e gera as
matrizes de resultado humano usadas pelas demais analises (concordancia
entre avaliadores e comparacao de 3 vias entre Checkov/LLM/Humano).

Pre-requisito (ver README.md desta pasta, passo 7): o formulario preenchido
de cada avaliador deve estar salvo como o UNICO arquivo .docx dentro de
    <set>/revisao_humana/privada/revisores/<codigo>/
(o mesmo lugar onde ja fica o mapa_ids.csv daquele avaliador). Nunca
commitar esse .docx preenchido (contem nome/e-mail do avaliador na secao de
identificacao) - confirme que a pasta privada/ esta no .gitignore antes de
rodar isto pela primeira vez em um novo checkout.

Uso:
    python3 extrator_revisao_humana.py <caminho_para_o_set>

Exemplos (rodando de dentro de common/revisao_humana/):
    python3 extrator_revisao_humana.py ../../training_set
    python3 extrator_revisao_humana.py ../../test_set

Gera, em <set>/analises/:
    matriz_resultados_humanos_bruta.csv  - uma linha por (avaliador, caso),
                                            resposta bruta normalizada por regra
    matriz_resultados_humanos.csv        - uma linha por caso, com o veredito
                                            por MAIORIA entre os 3 avaliadores,
                                            no mesmo formato de
                                            matriz_resultados_checkov.csv /
                                            matriz_resultados_llm.csv (para
                                            uso direto em metricas_por_regra.py)
    divergencias_avaliadores.csv         - casos/regras em que os 3 avaliadores
                                            deram 3 respostas diferentes (sem
                                            maioria) - precisam de revisao manual
    experiencia_avaliadores.csv          - anos de experiencia em TI, anos com
                                            AWS/Terraform, certificacoes e tempo
                                            medio de analise por avaliador
                                            (SOMENTE os codigos R1/R2/R3, nunca
                                            nome/e-mail - ver nota de privacidade
                                            abaixo)

Nota de privacidade: nome e e-mail do avaliador aparecem no formulario
preenchido, mas este script NUNCA le nem grava esses dois campos em nenhum
lugar - somente os campos de experiencia profissional (anonimos por
natureza) sao extraidos, e sempre associados apenas ao codigo R1/R2/R3.

Limitacao conhecida (documentar caso apareca na pratica): a extracao dos
campos de experiencia (anos de TI, anos de AWS/Terraform, certificacoes) e
best-effort via regex sobre o texto digitado livremente pelo avaliador ao
lado do rotulo do campo. Se o avaliador reformatar a linha de forma
inesperada, o campo correspondente fica em branco neste CSV e um aviso e
impresso - revise manualmente esses casos antes de reportar no TCC. Ja as
respostas por regra e o tempo de analise vem de celulas de tabela (extracao
robusta, nao depende de padrao de texto livre).
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path
from statistics import mean

from docx import Document

REVISORES = ["R1", "R2", "R3"]
REGRAS = ["CKV_FINOPS_01", "CKV_FINOPS_02", "CKV_FINOPS_03", "CKV_FINOPS_04A", "CKV_FINOPS_04B"]

CAMPOS_EXPERIENCIA = [
    ("anos_ti", r"Anos de experi[êe]ncia profissional em TI:\s*(.+)"),
    ("anos_aws_terraform", r"Anos de experi[êe]ncia trabalhando especificamente com AWS e/ou Terraform:\s*(.+)"),
    ("certificacoes", r"deixe em branco:\s*(.+)"),
]


def sem_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalizar_veredito(bruto):
    """Normaliza o texto digitado pelo avaliador para PASSED/FAILED/N/A.
    Retorna '' se a celula estiver vazia (nao preenchida), ou None se o
    texto nao for reconhecido - nunca adivinha, para revisao manual."""
    texto = sem_acentos(bruto.strip().lower())
    if texto == "":
        return ""
    if texto in {"aprovado", "aprovada", "aprov", "ok", "pass", "passed", "conforme", "sim"}:
        return "PASSED"
    if texto in {"falhou", "falha", "reprovado", "reprovada", "fail", "failed", "nao conforme", "naoconforme"}:
        return "FAILED"
    if texto in {"n/a", "na", "n.a.", "nao aplicavel", "naoaplicavel", "-"}:
        return "N/A"
    return None


def extrair_experiencia(paragrafos_texto):
    """paragrafos_texto: lista de strings (um por paragrafo do docx, na
    secao anterior a tabela). Retorna dict {campo: valor_ou_None}."""
    texto_completo = "\n".join(paragrafos_texto)
    resultado = {}
    for chave, padrao in CAMPOS_EXPERIENCIA:
        m = re.search(padrao, texto_completo)
        if not m:
            resultado[chave] = None
            continue
        valor = m.group(1).strip()
        valor = re.sub(r"_+", "", valor).strip()
        valor = valor.splitlines()[0].strip() if valor else ""
        resultado[chave] = valor if valor else None
    return resultado


def carregar_mapa(mapa_csv):
    mapa = {}
    with mapa_csv.open(encoding="utf-8") as f:
        leitor = csv.DictReader(f, delimiter=";")
        for linha in leitor:
            mapa[linha["id_publico"]] = linha
    return mapa


def encontrar_docx_preenchido(pasta):
    candidatos = sorted(pasta.glob("*.docx"))
    if not candidatos:
        return None, f"Nenhum .docx encontrado em {pasta}."
    if len(candidatos) > 1:
        nomes = ", ".join(c.name for c in candidatos)
        return candidatos[-1], (
            f"[AVISO] Mais de um .docx em {pasta} ({nomes}). "
            f"Usando o mais recente ({candidatos[-1].name}) - confirme se e o correto."
        )
    return candidatos[0], None


def processar_avaliador(codigo, set_root):
    pasta = set_root / "revisao_humana" / "privada" / "revisores" / codigo
    mapa_csv = pasta / "mapa_ids.csv"
    avisos = []

    if not mapa_csv.exists():
        avisos.append(f"[{codigo}] PULADO: {mapa_csv} nao existe.")
        return None, avisos

    docx_path, aviso_docx = encontrar_docx_preenchido(pasta)
    if aviso_docx:
        avisos.append(f"[{codigo}] {aviso_docx}")
    if docx_path is None:
        avisos.append(f"[{codigo}] PULADO: nenhum formulario preenchido encontrado em {pasta}.")
        return None, avisos

    mapa = carregar_mapa(mapa_csv)
    doc = Document(str(docx_path))

    if not doc.tables:
        avisos.append(f"[{codigo}] PULADO: {docx_path.name} nao contem nenhuma tabela.")
        return None, avisos
    tabela = doc.tables[0]
    cabecalho = tabela.rows[0].cells[0].text.strip().lower()
    if "id do plano" not in sem_acentos(cabecalho):
        avisos.append(
            f"[{codigo}] [AVISO] Primeira celula da tabela em {docx_path.name} nao contem "
            f"'ID do Plano' (encontrado: '{tabela.rows[0].cells[0].text.strip()}'). "
            "Confirme manualmente se a tabela certa foi lida."
        )

    linhas_dados = tabela.rows[1:]
    if len(linhas_dados) != 30:
        avisos.append(
            f"[{codigo}] [AVISO] Esperava 30 linhas de dados na tabela, encontrei {len(linhas_dados)}."
        )

    paragrafos_intro = [p.text for p in doc.paragraphs]
    experiencia = extrair_experiencia(paragrafos_intro)
    for chave, valor in experiencia.items():
        if valor is None:
            avisos.append(f"[{codigo}] [AVISO] Nao consegui extrair o campo de experiencia '{chave}' - preencher manualmente.")

    resultados_por_caso = {}
    tempos = []
    for linha in linhas_dados:
        celulas = linha.cells
        id_texto = celulas[0].text.strip()
        m = re.search(r"\d+", id_texto)
        if not m:
            avisos.append(f"[{codigo}] [AVISO] Nao consegui ler o ID do plano na linha '{id_texto}' - linha ignorada.")
            continue
        id_publico = m.group().zfill(2)

        info_mapa = mapa.get(id_publico)
        if info_mapa is None:
            avisos.append(f"[{codigo}] [AVISO] id_publico '{id_publico}' (linha '{id_texto}') nao encontrado em mapa_ids.csv.")
            continue
        arquivo_original = info_mapa["arquivo_original"]

        respostas = {}
        for i, regra in enumerate(REGRAS, start=1):
            bruto = celulas[i].text.replace("\n", " ").strip()
            valor = normalizar_veredito(bruto)
            if valor is None:
                avisos.append(
                    f"[{codigo}] [AVISO] Resposta nao reconhecida para {regra} no plano_{id_publico} "
                    f"({arquivo_original}): '{bruto}' - tratando como N/A preenchimento invalido, REVISAR."
                )
                valor = ""
            elif valor == "":
                avisos.append(f"[{codigo}] [AVISO] Celula vazia (nao preenchida) para {regra} no plano_{id_publico} ({arquivo_original}).")
            respostas[regra] = valor

        obs = celulas[6].text.replace("\n", " ").strip()
        tempo_bruto = celulas[7].text.replace("\n", " ").strip()
        tempo_num = None
        m_tempo = re.search(r"[\d,.]+", tempo_bruto)
        if m_tempo:
            try:
                tempo_num = float(m_tempo.group().replace(",", "."))
                tempos.append(tempo_num)
            except ValueError:
                pass

        resultados_por_caso[arquivo_original] = {
            "id_publico": id_publico,
            "respostas": respostas,
            "observacoes": obs,
            "tempo_min": "" if tempo_num is None else tempo_num,
        }

    experiencia["tempo_medio_min"] = f"{mean(tempos):.1f}" if tempos else ""
    return {"resultados": resultados_por_caso, "experiencia": experiencia}, avisos


def maioria(valores):
    """valores: lista com as 3 respostas (PASSED/FAILED/N/A/''), uma por
    avaliador, na mesma ordem de REVISORES. Retorna (valor_majoritario,
    houve_maioria). Celulas vazias/invalidas ('') NAO contam como voto."""
    votos = [v for v in valores if v]
    if not votos:
        return "", False
    contagem = {v: votos.count(v) for v in set(votos)}
    maior = max(contagem.values())
    vencedores = [v for v, c in contagem.items() if c == maior]
    if len(vencedores) == 1 and maior >= 2:
        return vencedores[0], True
    if len(votos) == 1:
        # so um avaliador respondeu essa regra nesse caso - usa a unica resposta,
        # mas sinaliza que nao houve maioria de fato (dado incompleto)
        return votos[0], False
    return "", False


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 extrator_revisao_humana.py <caminho_para_o_set>\n"
            "Exemplos: python3 extrator_revisao_humana.py ../../training_set\n"
            "          python3 extrator_revisao_humana.py ../../test_set"
        )

    SET_ROOT = Path(sys.argv[1]).resolve()
    ANALISES_DIR = SET_ROOT / "analises"
    ANALISES_DIR.mkdir(parents=True, exist_ok=True)

    todos_avisos = []
    por_avaliador = {}
    for codigo in REVISORES:
        dados, avisos = processar_avaliador(codigo, SET_ROOT)
        todos_avisos.extend(avisos)
        if dados is not None:
            por_avaliador[codigo] = dados

    if not por_avaliador:
        print("\n".join(todos_avisos))
        raise SystemExit("\nNenhum avaliador com formulario preenchido encontrado. Nada gerado.")

    # sanity check: todos os avaliadores presentes devem cobrir o mesmo conjunto de casos
    conjuntos = {codigo: set(d["resultados"].keys()) for codigo, d in por_avaliador.items()}
    referencia = next(iter(conjuntos.values()))
    for codigo, casos in conjuntos.items():
        if casos != referencia:
            todos_avisos.append(
                f"[AVISO] {codigo} avaliou um conjunto de casos diferente dos demais avaliadores presentes "
                f"(diferenca: {referencia.symmetric_difference(casos)})."
            )
    todos_casos = sorted(set().union(*conjuntos.values())) if conjuntos else []

    # ---- matriz bruta (uma linha por avaliador x caso) ----
    linhas_brutas = []
    for codigo, dados in por_avaliador.items():
        for arquivo_original, info in dados["resultados"].items():
            linha = {"ID do Caso": arquivo_original, "Avaliador": codigo}
            linha.update(info["respostas"])
            linha["Observacoes"] = info["observacoes"]
            linha["Tempo (min)"] = info["tempo_min"]
            linhas_brutas.append(linha)
    linhas_brutas.sort(key=lambda l: (l["ID do Caso"], l["Avaliador"]))

    colunas_brutas = ["ID do Caso", "Avaliador"] + REGRAS + ["Observacoes", "Tempo (min)"]
    with (ANALISES_DIR / "matriz_resultados_humanos_bruta.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_brutas, delimiter=";")
        w.writeheader()
        w.writerows(linhas_brutas)

    # ---- matriz agregada por maioria (mesmo formato de Checkov/LLM) ----
    linhas_agregadas = []
    linhas_divergencia = []
    for arquivo_original in todos_casos:
        linha = {"ID do Caso": arquivo_original}
        falhou_geral = False
        teve_sem_maioria = False
        for regra in REGRAS:
            valores = [por_avaliador[c]["resultados"].get(arquivo_original, {}).get("respostas", {}).get(regra, "")
                       for c in REVISORES if c in por_avaliador]
            valor_maioria, houve_maioria = maioria(valores)
            if not houve_maioria and any(valores):
                teve_sem_maioria = True
                linhas_divergencia.append({
                    "ID do Caso": arquivo_original, "Regra": regra,
                    **{c: por_avaliador[c]["resultados"].get(arquivo_original, {}).get("respostas", {}).get(regra, "")
                       for c in REVISORES if c in por_avaliador},
                })
                linha[regra] = "SEM_MAIORIA"
            else:
                linha[regra] = valor_maioria if valor_maioria else "N/A"
            if linha[regra] == "FAILED":
                falhou_geral = True
        linha["Veredito Humano"] = "FAILED" if falhou_geral else "PASSED"
        if teve_sem_maioria:
            linha["Veredito Humano"] += " (revisar - ha regra sem maioria)"
        linhas_agregadas.append(linha)

    colunas_agregadas = ["ID do Caso"] + REGRAS + ["Veredito Humano"]
    with (ANALISES_DIR / "matriz_resultados_humanos.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_agregadas, delimiter=";")
        w.writeheader()
        w.writerows(linhas_agregadas)

    colunas_div = ["ID do Caso", "Regra"] + REVISORES
    with (ANALISES_DIR / "divergencias_avaliadores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_div, delimiter=";")
        w.writeheader()
        w.writerows(linhas_divergencia)

    # ---- experiencia por avaliador (SEM nome/e-mail) ----
    linhas_exp = []
    for codigo, dados in por_avaliador.items():
        exp = dados["experiencia"]
        linhas_exp.append({
            "Avaliador": codigo,
            "Anos experiencia TI": exp.get("anos_ti") or "",
            "Anos experiencia AWS/Terraform": exp.get("anos_aws_terraform") or "",
            "Certificacoes": exp.get("certificacoes") or "",
            "Tempo medio de analise (min)": exp.get("tempo_medio_min") or "",
        })
    linhas_exp.sort(key=lambda l: l["Avaliador"])
    colunas_exp = ["Avaliador", "Anos experiencia TI", "Anos experiencia AWS/Terraform", "Certificacoes", "Tempo medio de analise (min)"]
    with (ANALISES_DIR / "experiencia_avaliadores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas_exp, delimiter=";")
        w.writeheader()
        w.writerows(linhas_exp)

    print(f"OK: {len(por_avaliador)} avaliador(es) processado(s): {', '.join(sorted(por_avaliador))}")
    print(f"OK: matriz bruta salva em {ANALISES_DIR / 'matriz_resultados_humanos_bruta.csv'}")
    print(f"OK: matriz agregada (maioria) salva em {ANALISES_DIR / 'matriz_resultados_humanos.csv'}")
    print(f"OK: experiencia dos avaliadores salva em {ANALISES_DIR / 'experiencia_avaliadores.csv'}")
    if linhas_divergencia:
        print(f"[ATENCAO] {len(linhas_divergencia)} caso(s)/regra(s) sem maioria entre os avaliadores - ver divergencias_avaliadores.csv")
    if todos_avisos:
        print("\n--- AVISOS ---")
        for a in todos_avisos:
            print(a)


if __name__ == "__main__":
    main()
