const {
  Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle,
  Math: M, MathRun, MathSubScript, MathSuperScript, MathSum,
} = require("docx");

const BODY = "Times New Roman";
const SZ = 22, BLACK = "000000";

const t = (text, o = {}) =>
  new TextRun({ text, font: BODY, size: SZ, color: BLACK, ...o });

const body = (text, o = {}) => new Paragraph({
  spacing: { after: 130, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: [t(text, o)],
});

const lead = (label, text) => new Paragraph({
  spacing: { after: 130, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: [t(label + "  ", { bold: true }), t(text)],
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 170 },
  children: [t(text, { bold: true, size: 28 })],
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 110 },
  children: [t(text, { bold: true, size: 23 })],
});

// ---- math builders ----
const mr = (s) => new MathRun(s);
const sub = (b, s) => new MathSubScript({ children: [mr(b)], subScript: [mr(s)] });
const sup = (b, s) => new MathSuperScript({ children: [mr(b)], superScript: [mr(s)] });
const sum = (under, children) =>
  new MathSum({ children, subScript: [mr(under)] });

const eq = (children, trailing) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 140, after: 140 },
  children: [new M({ children }),
             ...(trailing ? [t("          " + trailing)] : [])],
});

// a left-indented model line, so a model block reads as one unit
const eqL = (children, trailing) => new Paragraph({
  indent: { left: 720 }, spacing: { before: 90, after: 90 },
  children: [new M({ children }),
             ...(trailing ? [t("          " + trailing)] : [])],
});

// ---- tables ----
const line = { style: BorderStyle.SINGLE, size: 6, color: BLACK };
const grid = { top: line, bottom: line, left: line, right: line,
               insideHorizontal: line, insideVertical: line };
const PAD = { top: 60, bottom: 60, left: 120, right: 120 };

function table(widths, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    columnWidths: widths,
    width: { size: total, type: WidthType.DXA },
    borders: grid,
    rows: rows.map((cells, r) => new TableRow({
      tableHeader: r === 0,
      children: cells.map((c, k) => new TableCell({
        width: { size: widths[k], type: WidthType.DXA },
        margins: PAD,
        children: [new Paragraph({
          spacing: { after: 0 },
          children: [t(String(c), { bold: r === 0 })],
        })],
      })),
    })),
  });
}

// the slide 18 taxonomy, rendered the same way every time
function classification(rows) {
  return table([3500, 4180],
    [["Axis", "This formulation"]].concat(rows));
}

const gap = () => new Paragraph({ spacing: { after: 100 }, children: [t("")] });

module.exports = { t, body, lead, h1, h2, mr, sub, sup, sum, eq, eqL,
                   table, classification, gap, BODY, SZ, BLACK };
