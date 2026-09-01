const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, PageOrientation, VerticalAlign,
  Header, Footer, PageNumber, LevelFormat, convertInchesToTwip
} = require("docx");
const fs = require("fs");
const path = require("path");

// ---------- Layout ----------
const PAGE_W = 11906; // A4 portrait width (twips) - swapped to landscape below
const PAGE_H = 16838; // A4 portrait height (twips)
const MARGIN = 620;

const TABLE_W = PAGE_W - 2 * MARGIN; // usable width once landscape (portrait height becomes width)
// after landscape swap, usable width = PAGE_H - margins (since width/height swap)
const USABLE_W = PAGE_H - 2 * MARGIN; // 16838 - 1240 = 15598

const COLS = [
  { key: "id", label: "ID do Plano", width: 1000 },
  { key: "r01", label: "CKV_FINOPS_01\nTags obrigatórias", width: 1750 },
  { key: "r02", label: "CKV_FINOPS_02\nValor da tag Ambiente", width: 1750 },
  { key: "r03", label: "CKV_FINOPS_03\nRegião us-east-1", width: 1750 },
  { key: "r04a", label: "CKV_FINOPS_04A\nEC2 família t (HML)", width: 1750 },
  { key: "r04b", label: "CKV_FINOPS_04B\nRDS família t (HML)", width: 1750 },
  { key: "obs", label: "Observações", width: 4348 },
  { key: "tempo", label: "Tempo de avaliação\n(minutos)", width: 1250 },
];
// sum check
const sum = COLS.reduce((a, c) => a + c.width, 0);
console.log("sum cols", sum, "usable", USABLE_W);

const GRAY = "D9D9D9";
const LIGHT = "F2F2F2";

function cellPara(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    children: [
      new TextRun({ text, bold: !!opts.bold, size: opts.size || 18 }),
    ],
  });
}

function headerCell(col) {
  const lines = col.label.split("\n");
  return new TableCell({
    width: { size: col.width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: GRAY },
    verticalAlign: VerticalAlign.CENTER,
    children: lines.map((l, i) =>
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: l, bold: true, size: 17 })],
      })
    ),
  });
}

function dataCell(col, rowShaded) {
  return new TableCell({
    width: { size: col.width, type: WidthType.DXA },
    shading: rowShaded ? { type: ShadingType.CLEAR, fill: LIGHT } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [cellPara(col.key === "id" ? "" : "", { size: 18 })],
  });
}

// ---------- Header intro paragraphs ----------
function h(text, level) {
  return new Paragraph({ heading: level, text, spacing: { before: 200, after: 100 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text, bold: !!opts.bold, italics: !!opts.italics, size: 21 })],
  });
}
function bullet(text) {
  return new Paragraph({
    spacing: { after: 60 },
    numbering: { reference: "regras-bullets", level: 0 },
    children: [new TextRun({ text, size: 21 })],
  });
}
function campo(rotulo, linhaPreenchimento) {
  return new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text: `${rotulo} ${linhaPreenchimento}`, size: 21 })],
  });
}

const introBlocks = [
  h("Formulário de Avaliação de Conformidade FinOps em Alterações de Infraestrutura (Terraform)", HeadingLevel.HEADING_1),
  p("Este formulário faz parte de um Trabalho de Conclusão de Curso (TCC) do MBA em Engenharia de Software (USP/Esalq), cujo objetivo é comparar o desempenho de três abordagens de validação de alterações de infraestrutura como código (IaC) quanto à conformidade com regras de FinOps: um modelo de linguagem (LLM), uma ferramenta de análise estática (Checkov) e avaliadores humanos especialistas."),
  p("Você foi convidado(a) a atuar como avaliador(a) humano(a) neste estudo. Sua tarefa é analisar 30 planos de alteração de infraestrutura (gerados pelo Terraform) e indicar, para cada um, se ele está em conformidade com cada uma das 5 regras de FinOps descritas abaixo."),

  h("Instruções", HeadingLevel.HEADING_2),
  p("1. Os planos estão nos arquivos plano_01.txt a plano_30.txt, na pasta \"planos\" que acompanha este formulário. Cada arquivo corresponde a uma linha da tabela deste formulário (mesmo número). A ordem e a numeração dos planos são exclusivas deste envio — não corresponda ou compare números de plano com os de outros avaliadores."),
  p("2. Avalie os planos de forma independente, na ordem que preferir, sem consultar outras pessoas ou ferramentas de análise durante a avaliação."),
  p("3. Para cada uma das 5 regras, marque \"Aprovado\" se o plano cumpre a regra, \"Falhou\" se a viola, ou \"N/A\" se a regra não se aplica (por exemplo, a regra de família de instância RDS não se aplica a um plano que não cria nenhum recurso RDS)."),
  p("4. A unidade de análise de cada plano é o conjunto de recursos que serão criados ou lidos (ações \"create\"/\"read\" no plano do Terraform) — ignore recursos marcados para exclusão (\"delete\") ou sem alteração (\"no-op\"), caso apareçam no texto renderizado."),
  p("5. Use a coluna \"Observações\" para registrar qualquer dúvida, ambiguidade ou detalhe relevante sobre sua decisão."),
  p("6. Anote na coluna \"Tempo de avaliação\" quantos minutos você levou para avaliar aquele plano especificamente (pode usar um cronômetro simples)."),
  p("7. Não é necessário revisar todos os 30 planos de uma só vez — você pode dividir a avaliação em mais de uma sessão."),
  p("8. As informações deste formulário serão tratadas de forma confidencial e usadas exclusivamente para fins acadêmicos deste TCC. Nas análises e no repositório do trabalho, você será identificado(a) apenas por um código anônimo (ex.: R1, R2, R3) — seu nome não será associado publicamente às suas respostas."),

  h("Regras de FinOps avaliadas", HeadingLevel.HEADING_2),
];

const regras = [
  "CKV_FINOPS_01 — Tags obrigatórias: os recursos principais (instâncias EC2, instâncias RDS e buckets S3) devem conter as tags \"Projeto\", \"Time Responsável\" e \"Ambiente\", todas preenchidas (não vazias).",
  "CKV_FINOPS_02 — Valores válidos de Ambiente: a tag \"Ambiente\" só pode conter o valor \"PRD\" ou \"HML\".",
  "CKV_FINOPS_03 — Região única: todo recurso deve ser provisionado exclusivamente na região \"us-east-1\".",
  "CKV_FINOPS_04A — Família t para EC2 em HML: se a tag \"Ambiente\" for \"HML\", instâncias EC2 devem pertencer à família \"t\" (ex.: t2.micro, t3.medium).",
  "CKV_FINOPS_04B — Família t para RDS em HML: se a tag \"Ambiente\" for \"HML\", instâncias RDS devem pertencer à família \"db.t\" (ex.: db.t3.micro).",
];

const idBlocks = [
  h("Identificação do revisor", HeadingLevel.HEADING_2),
  campo("Nome completo:", "______________________________________________"),
  campo("E-mail:", "______________________________________________"),
  campo("Data de início da avaliação: ____ / ____ / ______      Data de término:", "____ / ____ / ______"),

  h("Experiência profissional", HeadingLevel.HEADING_2),
  p("As perguntas abaixo ajudam a caracterizar o grupo de avaliadores deste estudo (reportado de forma agregada e anônima no TCC, nunca associado ao seu nome)."),
  campo("Anos de experiência profissional em TI:", "______"),
  campo("Anos de experiência trabalhando especificamente com AWS e/ou Terraform:", "______"),
  new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text: "Certificações relevantes (ex.: AWS Certified Solutions Architect, HashiCorp Terraform Associate, FinOps Certified Practitioner) — liste todas que possuir ou deixe em branco:", size: 21 })],
  }),
  new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "______________________________________________________________________", size: 21 })] }),

  h("Tabela de avaliação", HeadingLevel.HEADING_2),
];

// ---------- Table ----------
const headerRow = new TableRow({
  tableHeader: true,
  children: COLS.map(headerCell),
});

const dataRows = [];
for (let i = 1; i <= 30; i++) {
  const idStr = String(i).padStart(2, "0");
  const shaded = i % 2 === 0;
  const cells = COLS.map((col) => {
    if (col.key === "id") {
      return new TableCell({
        width: { size: col.width, type: WidthType.DXA },
        shading: shaded ? { type: ShadingType.CLEAR, fill: LIGHT } : undefined,
        verticalAlign: VerticalAlign.CENTER,
        children: [cellPara(`plano_${idStr}`, { bold: true, size: 18, align: AlignmentType.CENTER })],
      });
    }
    return dataCell(col, shaded);
  });
  dataRows.push(new TableRow({ children: cells }));
}

const table = new Table({
  width: { size: sum, type: WidthType.DXA },
  columnWidths: COLS.map((c) => c.width),
  rows: [headerRow, ...dataRows],
});

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "regras-bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: PAGE_W, height: PAGE_H, orientation: PageOrientation.LANDSCAPE },
          margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
        },
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Página ", size: 16 }),
                new TextRun({ children: [PageNumber.CURRENT], size: 16 }),
                new TextRun({ text: " de ", size: 16 }),
                new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16 }),
              ],
            }),
          ],
        }),
      },
      children: [
        ...introBlocks,
        ...regras.map(bullet),
        ...idBlocks,
        table,
      ],
    },
  ],
});

const OUT_PATH = path.join(__dirname, "Formulario_Revisao_FinOps.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT_PATH, buf);
  console.log("done ->", OUT_PATH);
});
