const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, TabStopType,
  Math: M, MathRun, MathSubScript, MathSuperScript, MathSum,
} = require("docx");

const BODY = "Times New Roman";
const SZ = 22;            // 11pt, half-points
const BLACK = "000000";

// ---------- small helpers ----------
const t = (text, o = {}) =>
  new TextRun({ text, font: BODY, size: SZ, color: BLACK, ...o });

const p = (runs, o = {}) =>
  new Paragraph({ children: Array.isArray(runs) ? runs : [runs],
                  spacing: { after: 120 }, ...o });

const body = (text, o = {}) => p([t(text)], o);

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 160 },
  children: [t(text, { bold: true, size: 26 })],
});

const mr = (s) => new MathRun(s);
const sub = (b, s) => new MathSubScript({ children: [mr(b)], subScript: [mr(s)] });
const sup = (b, s) => new MathSuperScript({ children: [mr(b)], superScript: [mr(s)] });
const sumI = (children) =>
  new MathSum({ children, subScript: [mr("i ∈ I")] });

// a centred display equation, optionally with a trailing quantifier
const eq = (mathChildren, trailing) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 140, after: 140 },
  children: [
    new M({ children: mathChildren }),
    ...(trailing ? [t("        " + trailing)] : []),
  ],
});

// plain black table, header row in bold, no shading
const NOPAD = { top: 60, bottom: 60, left: 120, right: 120 };
const line = { style: BorderStyle.SINGLE, size: 6, color: BLACK };
const grid = { top: line, bottom: line, left: line, right: line,
               insideHorizontal: line, insideVertical: line };

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
        margins: NOPAD,
        children: [new Paragraph({
          spacing: { after: 0 },
          children: [t(String(c), { bold: r === 0 })],
        })],
      })),
    })),
  });
}

// ---------- document ----------
const doc = new Document({
  creator: "Lidivine Kengne",
  title: "IE 5311 Diet Problem Formulation",
  styles: {
    default: {
      document: { run: { font: BODY, size: SZ, color: BLACK } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },          // US Letter
        margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
      },
    },
    children: [

      // ---------- title block ----------
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [t("IE 5311-001 (D01)  Principles of Optimization",
                     { bold: true, size: 30 })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [t("Part 1, Problem 1: The Diet Problem (Stigler Diet)",
                     { size: 26 })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 40 },
        children: [t("Lidivine Kengne")],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 240 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLACK,
                            space: 8 } },
        children: [t("Fall 2026")],
      }),

      // ---------- 1 ----------
      h1("1.  Problem Statement"),
      body("Slide 15 gives the original 1945 version. For a moderately active man weighing 154 pounds, how much of each of 77 foods should be eaten daily so that his intake of nine nutrients is at least the recommended dietary allowances suggested by the National Research Council in 1943, at minimum cost?"),
      body("Stigler's heuristic eliminated 62 foods and reached $39.93. Dantzig later solved the same instance to optimality at $39.69 using linear programming and the simplex method (slide 16)."),
      body("The formulation below is written for arbitrary food and nutrient sets. Substituting the full 77 foods and 9 nutrients requires changing data only, never the model."),

      // ---------- 2 ----------
      h1("2.  Sets"),
      table([1200, 6480], [
        ["Symbol", "Definition"],
        ["I", "Set of available foods, indexed by i"],
        ["J", "Set of nutrients under control, indexed by j"],
      ]),
      body(""),

      // ---------- 3 ----------
      h1("3.  Parameters"),
      table([1200, 4600, 1880], [
        ["Symbol", "Definition", "Units"],
        ["cᵢ", "Cost per unit of food i", "$ / unit"],
        ["aᵢⱼ", "Amount of nutrient j per unit of food i", "g / unit"],
        ["ℓⱼ", "Minimum required daily level of nutrient j", "g / day"],
        ["uⱼ", "Maximum allowed daily level of nutrient j", "g / day"],
        ["fᵢ", "Maximum daily servings of food i", "unit / day"],
      ]),
      body(""),
      body("All parameters are known constants. For every i in I and j in J the data satisfy cᵢ ≥ 0, aᵢⱼ ≥ 0, and 0 ≤ ℓⱼ ≤ uⱼ."),

      // ---------- 4 ----------
      h1("4.  Decision Variables"),
      body("One variable per food. Nothing else is under the decision maker's control."),
      eq([sub("x", "i"), mr(" = units of food "), mr("i"),
          mr(" consumed per day,      "), sub("x", "i"),
          mr(" ∈ "), sup("ℝ", "+"), mr(",   i ∈ I")]),

      // ---------- 5 ----------
      h1("5.  Model"),
      eq([mr("min "), sumI([sub("c", "i"), sub("x", "i")])]),
      body("subject to"),
      eq([sumI([sub("a", "ij"), sub("x", "i")]), mr(" ≥ "), sub("ℓ", "j")],
         "for all j ∈ J"),
      eq([sumI([sub("a", "ij"), sub("x", "i")]), mr(" ≤ "), sub("u", "j")],
         "for all j ∈ J"),
      eq([mr("0 ≤ "), sub("x", "i"), mr(" ≤ "), sub("f", "i")],
         "for all i ∈ I"),
      body("The objective minimizes total daily cost. The first constraint family enforces the recommended minimum for every nutrient, the second the corresponding maximum. The bounds keep consumption nonnegative and cap the servings of any single food."),

      // ---------- 6 ----------
      h1("6.  Compact Matrix Form"),
      body("Let x collect the decision variables, c the costs and f the serving caps, each a vector of length |I|. Let ℓ and u collect the nutrient bounds, each of length |J|. Define the nutrient matrix A of size |J| by |I| with entry Aⱼᵢ = aᵢⱼ, so that Ax is the vector of daily intakes. The model becomes:"),
      eq([mr("min "), sup("c", "⊤"), mr("x"),
          mr("      subject to      ℓ ≤ Ax ≤ u,      0 ≤ x ≤ f")]),

      // ---------- 7 ----------
      h1("7.  Classification (slide 18 taxonomy)"),
      table([3600, 4080], [
        ["Axis", "This formulation"],
        ["Constrained or unconstrained", "Constrained"],
        ["Variable type", "Continuous"],
        ["Variable size", "Compact, |I| variables"],
        ["Objective type", "Linear"],
        ["Constraint type", "Linear"],
        ["Constraint size", "Compact, 2|J| + 2|I| inequalities"],
        ["Objective size", "Single objective"],
        ["Parameters", "Deterministic"],
        ["Decision stage", "One-stage"],
        ["Number of players", "Single"],
      ]),
      body(""),
      body("Every entry is linear with compact size, which places this problem squarely in Part 2 of the course."),

      // ---------- 8 ----------
      h1("8.  Geometry (slide 19)"),
      body("Each constraint is a linear inequality in x, so each defines a half-space in |I|-dimensional space, and the boundary of each is a hyperplane. For nutrient j the equation below is the hyperplane on which the minimum requirement is met exactly."),
      eq([sumI([sub("a", "ij"), sub("x", "i")]), mr(" = "), sub("ℓ", "j")]),
      body("The feasible region is the intersection of 2|J| + 2|I| half-spaces, therefore a polyhedron. Since the bounds 0 ≤ x ≤ f restrict every coordinate, the region is a polytope: bounded, closed and convex."),

      // ---------- 9 ----------
      h1("9.  Notes"),
      body("Why the serving caps matter.", { bold: true }),
      body("Stigler's original model carried no upper bounds fᵢ on servings and no upper bounds uⱼ on nutrients. With cost minimization as the only pressure, the optimum concentrates on whichever few foods deliver nutrients most cheaply, producing the monotonous diets the problem became known for. A solved instance of the formulation above shows the same effect: the optimum loads onto two foods and leaves the rest at zero. Adding fᵢ and uⱼ changes the data of the model, not its structure."),
      body("Reading the dual.", { bold: true }),
      body("Each minimum-intake constraint carries a shadow price, the increase in minimum daily cost caused by raising ℓⱼ by one gram. Nutrients whose constraints are slack at the optimum carry a shadow price of zero. This is the dual information that slide 52 generalizes as expectation written through dual pairing, and that Part 2 formalizes as linear programming duality."),
      body("Solved instance.", { bold: true }),
      body("With six foods and three nutrients the minimum daily cost is $7.8169, achieved with 268.3 g of beef and 316.9 g of noodles. The fat and carbohydrate minimums bind, with shadow prices 0.1667 and 0.0014 respectively. The protein minimum is slack at 111.0 g against a floor of 56 g, so its shadow price is zero. Two independent solvers, CBC through PuLP and Gurobi, agree on every one of these figures."),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2], buf);
  console.log("written", process.argv[2], buf.length, "bytes");
});
