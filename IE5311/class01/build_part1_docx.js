const fs = require("fs");
const { Document, Packer, Paragraph, AlignmentType, BorderStyle,
        PageBreak, Math: M } = require("docx");
const H = require("./build_docx_helpers.js");
const { t, body, lead, h1, h2, mr, sub, sup, sum, eq, eqL,
        table, classification, gap } = H;

const IN = "∈", LE = "≤", GE = "≥", NE = "≠";
const SUBSET = "⊂", CUP = "∪", EMPTY = "∅", TIMES = "×";
const R = "ℝ", ELL = "ℓ", DELTA = "δ", NOTIN = "∉";

const children = [];
const push = (...xs) => xs.forEach((x) => children.push(x));

// ======================================================================
// TITLE
// ======================================================================
push(
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 70 },
    children: [t("IE 5311-001 (D01)  Principles of Optimization", { bold: true, size: 32 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 70 },
    children: [t("Part 1: Classic Problems and Formulations", { size: 27 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 50 },
    children: [t("Problems 1 through 4, with the total unimodularity exploration")] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 50 },
    children: [t("Lidivine Kengne")] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 260 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 8 } },
    children: [t("Fall 2026   |   Instructor: Ningji Wei")] }),
);

// ======================================================================
// 0. CONVENTIONS
// ======================================================================
push(
  h1("0.  Conventions Used Throughout"),
  body("Every formulation below states, in order: the index sets, the parameters defined over those sets with their units, the decision variables with their domains, the objective as a sum over an index set, and each constraint written once under a quantifier. No constraint is written out for a specific numerical value."),
  body("Each formulation is then classified on the taxonomy introduced on slides 8 through 10, the same taxonomy the instructor applies to the diet problem on slide 18, to shortest path on slide 27 and to the travelling salesman formulation on slide 32."),
  body("Numerical results quoted in the notes come from solved instances. Every instance was solved with PuLP and the CBC solver, which requires no licence. Where a second check was useful, Gurobi was run on the same model and agreed."),
);

// ======================================================================
// 1. DIET
// ======================================================================
push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("1.  Problem 1: The Diet Problem (Stigler Diet)"),
  h2("1.1  Statement"),
  body("Slide 15 gives the original 1945 version. For a moderately active man weighing 154 pounds, how much of each of 77 foods should be eaten daily so that his intake of nine nutrients is at least the recommended dietary allowances suggested by the National Research Council in 1943, at minimum cost?"),
  body("Stigler's heuristic eliminated 62 foods and reached $39.93. Dantzig later solved the same instance to optimality at $39.69 using linear programming and the simplex method (slide 16)."),

  h2("1.2  Sets"),
  table([1250, 6430], [
    ["Symbol", "Definition"],
    ["I", "Set of available foods, indexed by i"],
    ["J", "Set of nutrients under control, indexed by j"],
  ]), gap(),

  h2("1.3  Parameters"),
  table([1250, 4550, 1880], [
    ["Symbol", "Definition", "Units"],
    ["cᵢ", "Cost per unit of food i", "$ / unit"],
    ["aᵢⱼ", "Amount of nutrient j per unit of food i", "g / unit"],
    ["ℓⱼ", "Minimum required daily level of nutrient j", "g / day"],
    ["uⱼ", "Maximum allowed daily level of nutrient j", "g / day"],
    ["fᵢ", "Maximum daily servings of food i", "unit / day"],
  ]), gap(),
  body(`All parameters are known constants, with cᵢ ${GE} 0, aᵢⱼ ${GE} 0 and 0 ${LE} ℓⱼ ${LE} uⱼ for every i ${IN} I and j ${IN} J.`),

  h2("1.4  Decision Variables"),
  eq([sub("x", "i"), mr(" = units of food i consumed per day,      "),
      sub("x", "i"), mr(` ${IN} `), sup(R, "+"), mr(`,   i ${IN} I`)]),

  h2("1.5  Model"),
  eqL([mr("min  "), sum(`i ${IN} I`, [sub("c", "i"), sub("x", "i")])]),
  body("subject to"),
  eqL([sum(`i ${IN} I`, [sub("a", "ij"), sub("x", "i")]), mr(` ${GE} `), sub(ELL, "j")], `for all j ${IN} J`),
  eqL([sum(`i ${IN} I`, [sub("a", "ij"), sub("x", "i")]), mr(` ${LE} `), sub("u", "j")], `for all j ${IN} J`),
  eqL([mr(`0 ${LE} `), sub("x", "i"), mr(` ${LE} `), sub("f", "i")], `for all i ${IN} I`),
  gap(),
  body("The objective minimizes total daily cost. The first constraint family enforces the recommended minimum for every nutrient, the second the corresponding maximum. The bounds keep consumption nonnegative and cap the servings of any single food."),

  h2("1.6  Compact Matrix Form"),
  body("Let x, c and f be vectors of length |I| holding the variables, costs and serving caps. Let ℓ and u be vectors of length |J| holding the nutrient bounds. Define the nutrient matrix A of size |J| by |I| with entry Aⱼᵢ = aᵢⱼ, so that Ax is the vector of daily intakes."),
  eq([mr("min  "), sup("c", "⊤"), mr("x"),
      mr(`      subject to      ℓ ${LE} Ax ${LE} u,      0 ${LE} x ${LE} f`)]),

  h2("1.7  Classification"),
  classification([
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
  ]), gap(),

  h2("1.8  Geometry (slide 19)"),
  body("Each constraint is a linear inequality in x, so each defines a half-space, and the boundary of each is a hyperplane. For nutrient j the equation below is the hyperplane on which the minimum requirement is met exactly."),
  eq([sum(`i ${IN} I`, [sub("a", "ij"), sub("x", "i")]), mr(" = "), sub(ELL, "j")]),
  body(`The feasible region is the intersection of 2|J| + 2|I| half-spaces, therefore a polyhedron. Since 0 ${LE} x ${LE} f bounds every coordinate, the region is a polytope: bounded, closed and convex.`),

  h2("1.9  Notes"),
  lead("Solved instance.", "With six foods and three nutrients the minimum daily cost is $7.8169, achieved with 268.3 g of beef and 316.9 g of noodles and nothing else. The fat and carbohydrate minimums bind, with shadow prices 0.1667 and 0.0014. The protein minimum is slack at 111.0 g against a floor of 56 g, so its shadow price is zero."),
  lead("Why the serving caps matter.", "Stigler's original model carried no caps fᵢ and no nutrient ceilings uⱼ. Under cost minimization alone the optimum concentrates on whichever few foods deliver nutrients most cheaply, which is why the solved instance above loads onto two foods. Adding fᵢ and uⱼ changes the data, not the structure."),
  lead("Removing a food.", "Dropping one food from I and re-solving is a data change, so the model code is untouched. Removing beef makes the instance infeasible rather than merely costlier: without beef the 45 g fat floor requires so much chicken that the 120 g protein ceiling is breached first. Feasibility, not cost, is the binding consideration."),
);

// ======================================================================
// 2. SHORTEST PATH
// ======================================================================
push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("2.  Problem 2: Shortest Path"),
  h2("2.1  Statement"),
  body("Slide 24. An emergency has occurred in region t. The central policy department at location s must dispatch a team to reach the site as quickly as possible."),

  h2("2.2  Sets"),
  table([1250, 6430], [
    ["Symbol", "Definition"],
    ["V", "Set of nodes (locations), indexed by i and j"],
    [`A ${SUBSET} V ${TIMES} V`, "Set of directed arcs, a typical arc written (i, j)"],
    [`${DELTA}⁺(i)`, "Out-neighborhood of node i, the set of j with (i, j) in A"],
    [`${DELTA}⁻(i)`, "In-neighborhood of node i, the set of j with (j, i) in A"],
  ]), gap(),
  body("The out-neighborhood and in-neighborhood notation follows the directed-graph terminology introduced on slide 23."),

  h2("2.3  Parameters"),
  table([1250, 4550, 1880], [
    ["Symbol", "Definition", "Units"],
    ["cᵢⱼ", "Travel time along arc (i, j)", "minutes"],
    ["s", "Source node, the dispatching department", "node"],
    ["t", "Sink node, the emergency site", "node"],
    ["bᵢ", "Net supply at node i: +1 at s, −1 at t, 0 elsewhere", "units of flow"],
  ]), gap(),

  h2("2.4  Decision Variables"),
  eq([sub("x", "ij"), mr(` = 1 if arc (i, j) is traversed, 0 otherwise,   (i, j) ${IN} A`)]),

  h2("2.5  Model"),
  eqL([mr("min  "), sum(`(i,j) ${IN} A`, [sub("c", "ij"), sub("x", "ij")])]),
  body("subject to"),
  eqL([sum(`j ${IN} ${DELTA}⁺(i)`, [sub("x", "ij")]), mr(" − "),
       sum(`j ${IN} ${DELTA}⁻(i)`, [sub("x", "ji")]), mr(" = "), sub("b", "i")],
      `for all i ${IN} V`),
  eqL([sub("x", "ij"), mr(` ${IN} {0, 1}`)], `for all (i, j) ${IN} A`),
  gap(),
  body("The single constraint family is flow conservation. One unit of flow is injected at s, removed at t, and conserved everywhere else. Writing the right-hand side as the indexed parameter bᵢ rather than as three separate cases keeps the model to one line."),

  h2("2.6  Is the Formulation Exact? (slide 25)"),
  body("Slide 25 asks whether this formulation is exact. Two questions hide inside that one."),
  body("First, does every feasible point correspond to a genuine s-to-t path? A feasible integer solution decomposes into one s-to-t path plus, possibly, some directed cycles that are arc-disjoint from the path. They need not be node-disjoint from it: flow conservation permits a node to carry two units in and two units out, so a node may be touched by both the path and a cycle. Since arc costs here are nonnegative, dropping any such cycle can only reduce cost, so an optimal solution carries no cycle and is a path. With negative cycles present the formulation would not be exact, which is a condition worth stating explicitly."),
  body("Second, and this is the interesting question, what happens if the integrality requirement is dropped? Replacing the binary domain by the interval [0, 1] gives a linear program. On a solved six-node instance that linear program returns cost 14.0 with every arc variable equal to 0 or 1, matching the integer program exactly. The integrality gap is zero. Section 5 explains why this is guaranteed rather than lucky."),

  h2("2.7  Classification (slide 27)"),
  classification([
    ["Constrained or unconstrained", "Constrained"],
    ["Variable type", "Binary"],
    ["Variable size", "Compact, |A| variables"],
    ["Objective type", "Linear"],
    ["Constraint type", "Linear"],
    ["Constraint size", "Compact, |V| equalities"],
    ["Objective size", "Single objective"],
    ["Parameters", "Deterministic"],
    ["Decision stage", "One-stage"],
    ["Number of players", "Single"],
  ]), gap(),

  h2("2.8  Notes"),
  lead("Solved instance.", "A six-node network with nine arcs gives an optimal route of cost 14.0 using arcs (s, b), (b, d) and (d, t). The linear programming relaxation returns the same route at the same cost, with no fractional variable anywhere."),
  lead("Size.", "The constraint count is |V|, one per node, independent of how the arcs are arranged. This is what makes shortest path tractable at scales where the travelling salesman problem of Section 3 is not."),
);

// ======================================================================
// 3. TSP
// ======================================================================
push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("3.  Problem 3: The Travelling Salesman Problem"),
  h2("3.1  Statement"),
  body("Slide 29. In a complete undirected graph, a team must visit a set of locations and return to its starting point while minimizing the total travel distance."),

  h2("3.2  Sets"),
  table([1250, 6430], [
    ["Symbol", "Definition"],
    ["V", "Set of cities, indexed by i and j, with n = |V|"],
    ["E", "Set of edges {i, j} with i < j, one per unordered pair"],
    [`${DELTA}(i)`, "Set of edges incident to city i"],
    [`E(S)`, "Set of edges with both endpoints inside the subset S"],
    [`${DELTA}(S)`, "Set of edges with exactly one endpoint inside S, the cut of S"],
  ]), gap(),

  h2("3.3  Parameters"),
  table([1250, 4550, 1880], [
    ["Symbol", "Definition", "Units"],
    ["cᵢⱼ", "Distance between cities i and j, symmetric", "distance"],
    ["n", "Number of cities, n = |V|", "count"],
  ]), gap(),

  h2("3.4  Decision Variables"),
  eq([sub("x", "ij"), mr(` = 1 if edge {i, j} lies on the tour, 0 otherwise,   {i, j} ${IN} E`)]),

  h2("3.5  Dantzig, Fulkerson and Johnson Formulation"),
  eqL([mr("min  "), sum(`{i,j} ${IN} E`, [sub("c", "ij"), sub("x", "ij")])]),
  body("subject to"),
  eqL([sum(`j ${IN} V \\ {i}`, [sub("x", "ij")]), mr(" = 2")], `for all i ${IN} V`),
  eqL([sum(`{i,j} ${IN} E(S)`, [sub("x", "ij")]), mr(` ${LE} |S| − 1`)],
      `for all S ${SUBSET} V with 2 ${LE} |S| ${LE} n − 1`),
  eqL([sub("x", "ij"), mr(` ${IN} {0, 1}`)], `for all {i, j} ${IN} E`),
  gap(),
  body("The first family is the degree condition: every city is touched by exactly two tour edges. The second family is subtour elimination: no proper subset S of cities may contain enough selected edges to close a cycle among themselves. Together they characterize exactly the Hamiltonian tours."),
  body("An equivalent statement uses cuts rather than interiors. Requiring at least two selected edges to cross the boundary of every proper nonempty subset forbids the same disconnected solutions:"),
  eq([sum(`{i,j} ${IN} ${DELTA}(S)`, [sub("x", "ij")]), mr(` ${GE} 2`),
      mr(`      for all S with ${EMPTY} ${NE} S ${SUBSET} V`)]),

  h2("3.6  Classification (slide 32)"),
  classification([
    ["Constrained or unconstrained", "Constrained"],
    ["Variable type", "Binary"],
    ["Variable size", "Compact, n(n − 1)/2 variables"],
    ["Objective type", "Linear"],
    ["Constraint type", "Linear"],
    ["Constraint size", "Huge but finite, on the order of 2ⁿ subtour constraints"],
    ["Objective size", "Single objective"],
    ["Parameters", "Deterministic"],
    ["Decision stage", "One-stage"],
    ["Number of players", "Single"],
  ]), gap(),
  body("The constraint size is the entire difficulty. For thirty cities the subtour family already holds more than a billion members, so the model cannot be written down, let alone handed to a solver."),

  h2("3.7  How to Solve It (slides 33 and 34)"),
  body("The constraints are not written down. They are generated on demand, in a loop between a master problem and a subproblem."),
  lead("Master problem.", "Minimize the tour length subject to the degree constraints and whichever subtour constraints have been generated so far. This is a relaxation of the true problem, since it omits constraints, so its optimal value is a lower bound."),
  lead("Subproblem (separation).", "Take the master solution and ask whether any subtour constraint is violated. For an integer master solution this is answered by computing the connected components of the selected edges. One component means a tour and the loop stops. Two or more components means each one yields a violated constraint, which is added to the master."),
  lead("Proof of finite convergence.", "The subtour family is finite, with fewer than 2ⁿ members. Each iteration that does not terminate adds at least one constraint that the current master solution violates, so that constraint was not present before and is never added twice. The number of iterations is therefore bounded by the size of the family, and the loop terminates."),
  lead("Proof of correctness.", "The loop stops only when the master solution violates no subtour constraint. At that moment the solution satisfies every degree constraint and every subtour constraint, so it is feasible for the full formulation. Its value is also the optimal value of a relaxation of the full formulation, hence a lower bound on the true optimum. A feasible solution whose value equals a valid lower bound is optimal."),
  lead("Solved instance.", "On a six-city Euclidean instance the first master solve returns length 18.4311 split into two triangles, {1, 5, 6} and {2, 3, 4}. Both components are cut off, and the second master solve returns a single tour of length 18.4907. Two master solves and two generated constraints, against a subtour family of 56 members for six cities."),

  h2("3.8  The Miller, Tucker and Zemlin Alternative (slide 30)"),
  body("Slide 30 notes a second formulation that describes the same feasible solutions while being compact rather than exponential. Working on the directed version with variables xᵢⱼ for ordered pairs, introduce continuous position variables uᵢ recording where city i falls in the tour order."),
  eqL([sum(`j ${NE} i`, [sub("x", "ij")]), mr(" = 1")], `for all i ${IN} V`),
  eqL([sum(`i ${NE} j`, [sub("x", "ij")]), mr(" = 1")], `for all j ${IN} V`),
  eqL([sub("u", "i"), mr(" − "), sub("u", "j"), mr(" + n "), sub("x", "ij"),
       mr(` ${LE} n − 1`)], `for all i ${NE} j in V \\ {1}`),
  eqL([mr(`2 ${LE} `), sub("u", "i"), mr(` ${LE} n`)], `for all i ${IN} V \\ {1}`),
  gap(),
  body("The position constraints number on the order of n² rather than 2ⁿ, so the whole model fits in memory. The cost appears elsewhere. Slide 30 states that the two describe the same feasible solution space while one is tighter than the other, without saying which one. I measured it on the six-city instance rather than assume a direction. Both formulations were built in their directed form over the same distance matrix, and integrality was dropped from each. The full Dantzig, Fulkerson and Johnson relaxation carries 56 subtour rows and returns a bound of 18.4907, which equals the integer optimum exactly on this instance. The Miller, Tucker and Zemlin relaxation carries 20 ordering rows and returns 18.1489, a gap of 0.3418 below the optimum. So the exponential formulation is the tighter one here and the compact formulation is the smaller one. Tighter bounds prune more of the branch-and-bound tree, which is why the exponential formulation with generated constraints is normally preferred despite never being written out in full. One six-city instance supports the direction of this comparison, not its magnitude at any other size."),
  lead("A caution on relaxation bounds.", "On the six-city instance above, dropping the subtour constraints entirely and relaxing integrality gives 18.4311 against a true optimum of 18.4907, only 0.32 percent below. That solution happened to be integral, and it failed to be a tour by being disconnected rather than by being fractional. Both failure modes occur; do not assume a relaxation fails only through fractional values."),
);

// ======================================================================
// 4. FACILITY LOCATION
// ======================================================================
push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("4.  Problem 4: Facility Location"),
  h2("4.1  Statement"),
  body("Slide 37. A company must decide which facilities to open and how to serve a set of customers from the open facilities, while minimizing the total facility-opening and transportation costs."),

  h2("4.2  Sets"),
  table([1250, 6430], [
    ["Symbol", "Definition"],
    ["F", "Set of candidate facility sites, indexed by i"],
    ["C", "Set of customers to be served, indexed by j"],
  ]), gap(),

  h2("4.3  Parameters"),
  table([1250, 4550, 1880], [
    ["Symbol", "Definition", "Units"],
    ["fᵢ", "Fixed cost of opening facility i", "$"],
    ["cᵢⱼ", "Cost of serving all of customer j's demand from facility i", "$"],
  ]), gap(),

  h2("4.4  Decision Variables"),
  eq([sub("y", "i"), mr(` = 1 if facility i is opened, 0 otherwise,   i ${IN} F`)]),
  eq([sub("x", "ij"), mr(` = fraction of customer j's demand served from facility i,   i ${IN} F, j ${IN} C`)]),

  h2("4.5  Single-Level Model"),
  eqL([mr("min  "), sum(`i ${IN} F`, [sub("f", "i"), sub("y", "i")]), mr(" + "),
       sum(`i ${IN} F`, [sum(`j ${IN} C`, [sub("c", "ij"), sub("x", "ij")])])]),
  body("subject to"),
  eqL([sum(`i ${IN} F`, [sub("x", "ij")]), mr(" = 1")], `for all j ${IN} C`),
  eqL([sub("x", "ij"), mr(` ${LE} `), sub("y", "i")], `for all i ${IN} F, j ${IN} C`),
  eqL([sub("x", "ij"), mr(` ${GE} 0,    `), sub("y", "i"), mr(` ${IN} {0, 1}`)],
      `for all i ${IN} F, j ${IN} C`),
  gap(),
  body("The demand constraints require every customer to be fully served. The linking constraints forbid serving anyone from a closed facility. Note that the assignment variables need no integrality restriction: with a fixed choice of open facilities the remaining problem is a transportation problem whose optimum assigns each customer entirely to its cheapest open facility."),

  h2("4.6  The Two-Player Reading (slide 38)"),
  body("Slide 38 presents this problem as a two-player problem, and the framing is worth taking seriously. The company is the leader and chooses which facilities to open. Each customer is a follower and, once the open set is known, independently picks the cheapest open facility. Writing the leader's problem with the followers' response embedded:"),
  eq([mr("min  "), sum(`i ${IN} F`, [sub("f", "i"), sub("y", "i")]), mr(" + "),
      sum(`j ${IN} C`, [mr("min "), sub("c", "ij")])]),
  body(`where the inner minimum is taken over the open facilities, those i ${IN} F with yᵢ = 1, and the leader must open at least one facility. The followers act after the leader and act independently of one another, which is why the inner minimum separates across customers.`),
  body("The single-level model of Section 4.5 is a valid reformulation of this two-player problem, but the reason deserves care. It works because the leader and the followers want the same thing: both prefer lower transportation cost. When objectives are aligned, the leader can simply choose the assignment directly and the followers have no reason to object. Change the followers' objective, for instance by letting customers care about distance while the company cares about money, and the single-level model stops being equivalent. The problem then becomes a genuine bilevel program, which is a materially harder object."),
  lead("Verification.", "On a four-facility, five-customer instance the single-level model returns cost 46.0, opening F1 and F3. Enumerating all fifteen possible open sets and letting each customer pick its own cheapest option also returns 46.0. The optimal values agree, which is the claim being tested. The optimal solutions need not: three different open sets attain 46.0, namely {F2}, {F1, F2} and {F1, F3}. A reformulation preserves optimal value, not the identity of the solution returned."),

  h2("4.7  Classification"),
  classification([
    ["Constrained or unconstrained", "Constrained"],
    ["Variable type", "Mixed: binary yᵢ, continuous xᵢⱼ"],
    ["Variable size", "Compact, |F| + |F||C| variables"],
    ["Objective type", "Linear"],
    ["Constraint type", "Linear"],
    ["Constraint size", "Compact, |C| + |F||C| constraints"],
    ["Objective size", "Single objective"],
    ["Parameters", "Deterministic"],
    ["Decision stage", "Two-stage in the two-player reading, one-stage once reformulated"],
    ["Number of players", "Leader plus |C| followers, collapsing to a single player when objectives align"],
  ]), gap(),

  h2("4.8  Why the Linking Constraint Is Written the Long Way"),
  body("The linking constraints could be aggregated. Instead of |F||C| separate inequalities, one per facility would suffice:"),
  eq([sum(`j ${IN} C`, [sub("x", "ij")]), mr(` ${LE} |C| `), sub("y", "i"),
      mr(`      for all i ${IN} F`)]),
  body("This says the same thing about integer solutions and uses far fewer rows. It is also much worse. On the instance above, the disaggregated form gives a linear programming bound of 45.0 against an integer optimum of 46.0, a gap of 1.0. The aggregated form gives 28.0, a gap of 18.0. The aggregated version lets a facility be opened a tiny fraction of the way and still serve everybody, which costs almost nothing in the relaxation and tells the solver almost nothing."),
  body("This is the same lesson slide 30 raises for the travelling salesman problem. Two formulations can describe identical integer solutions and still differ enormously in how useful they are. Fewer constraints is not the objective. A tighter relaxation is."),
);

// ======================================================================
// 5. EXPLORATION
// ======================================================================
push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("5.  Exploration: Total Unimodularity (slide 26)"),
  body("Slide 26 marks this as an exploration topic: total unimodularity explains why the linear programming relaxation of the shortest path formulation is exact. This section works out what the term means and why the guarantee holds."),

  h2("5.1  The Question"),
  body("Section 2.6 observed something that should be surprising. The shortest path model asks for binary variables. Drop that requirement, allow any value in [0, 1], and solve the resulting linear program. The answer comes back binary anyway. No branching, no rounding, no luck required."),
  body("Integer programs are hard in general and linear programs are not, so a structural reason must be responsible. The reason is a property of the constraint matrix."),

  h2("5.2  Definition"),
  body("A matrix is totally unimodular when every square submatrix has determinant equal to 0, +1 or −1. The condition covers submatrices of every order, not only the full matrix, and a submatrix is obtained by deleting any set of rows and any set of columns. Note that every entry of a totally unimodular matrix is itself a submatrix of order one, so all entries lie in {0, +1, −1}."),

  h2("5.3  Why the Property Forces Integral Solutions"),
  body("The link between determinants and integrality runs through Cramer's rule. A vertex of the feasible polyhedron is determined by a square nonsingular subsystem Bx = d, so its coordinates are given by ratios of determinants, each with det(B) in the denominator. If det(B) is +1 or −1 and the data d are integers, every coordinate of the vertex is an integer."),
  body("The general statement is due to Hoffman and Kruskal. For an integral matrix A, the polyhedron defined by Ax ≤ b with x ≥ 0 has only integral vertices for every integral right-hand side b if and only if A is totally unimodular. The condition is both necessary and sufficient, which is stronger than the one-directional argument above."),
  body("Since a linear program with a bounded nonempty feasible region attains its optimum at a vertex, the simplex method applied to such a system returns an integral solution without being asked. The integer program and its relaxation have the same optimal value."),

  h2("5.4  The Incidence Matrix of a Directed Graph Is Totally Unimodular"),
  body("The constraint matrix of the shortest path formulation is the node-arc incidence matrix: rows indexed by nodes, columns by arcs, with +1 in the row of the tail, −1 in the row of the head, and 0 everywhere else. Each column therefore contains exactly one +1 and exactly one −1."),
  lead("Proof by induction on the order of the submatrix.", "Let B be a square submatrix of order k. For k = 1 the single entry is 0, +1 or −1 by construction, so the claim holds. For k > 1, three cases exhaust the possibilities."),
  body("Case one: some column of B is entirely zero. Then det(B) = 0 and the claim holds."),
  body("Case two: some column of B contains exactly one nonzero entry, necessarily +1 or −1. Expanding the determinant along that column gives det(B) = ±1 times the determinant of a submatrix of order k − 1, which lies in {0, +1, −1} by the induction hypothesis. The product does too."),
  body("Case three: every column of B contains both a +1 and a −1, since a column of the full matrix holds no more than that. Then every column sums to zero, so the sum of all rows of B is the zero vector. The rows are linearly dependent, B is singular, and det(B) = 0."),
  body("Every case yields a determinant in {0, +1, −1}, completing the induction."),
  lead("Numerical confirmation, and its limits.", "For the six-node, nine-arc instance of Section 2 the incidence matrix has 6 rows and 9 columns, so square submatrices exist at every order from 1 to 6. Enumerating all of them gives 5,004 determinants, and every one lies in {0, +1, −1}. The largest deviation from that set is exactly zero, not merely small. This confirms the theorem on one matrix. It does not prove the theorem, which is what the induction above is for, and an exhaustive check of this kind becomes impossible at any useful size: the submatrix count grows as the product of two binomial coefficients."),

  h2("5.5  The Consequence for Shortest Path"),
  body("The shortest path constraints are flow conservation equalities whose matrix is exactly this incidence matrix, together with simple bounds on the variables. Appending an identity block for the bounds preserves total unimodularity. The right-hand side consists of the integers +1, −1 and 0, together with the bounds 0 and 1. Hoffman and Kruskal therefore apply: every vertex of the relaxed feasible region is integral, so the linear program returns a binary solution and the relaxation is exact."),
  body("This is the guarantee behind the observation in Section 2.6, and it is the answer slide 26 points toward."),

  h2("5.6  Where the Property Fails"),
  body("Total unimodularity is fragile, and knowing where it breaks is as useful as knowing where it holds. The incidence matrix of an undirected odd cycle is the standard counterexample. For a triangle, the three-by-three matrix with rows (1, 1, 0), (0, 1, 1) and (1, 0, 1) has determinant 2, which lies outside {0, +1, −1}. That matrix is therefore not totally unimodular, and the associated relaxations admit fractional vertices, the familiar all-one-half solution."),
  body("The travelling salesman problem inherits this failure. Its degree constraints are undirected incidence conditions, and its subtour constraints are worse still. No total unimodularity argument is available, the relaxation is not exact, and branch and bound becomes necessary. The contrast between Sections 2 and 3 is precisely the contrast between a matrix that has this property and one that does not."),

  h2("5.7  Sufficient Conditions Worth Knowing"),
  body("Checking every square submatrix is exponential work, so usable criteria matter. Ghouila-Houri gave a characterization in 1962: a matrix is totally unimodular if and only if every subset of its rows can be split into two parts such that, in each column, the sum over the first part minus the sum over the second part always lies in {−1, 0, +1}. A convenient sufficient condition also applies: a matrix with entries in {0, +1, −1}, at most two nonzero entries per column, and rows separable into two groups so that columns with two entries of equal sign have them in different groups while columns with two entries of opposite sign have them in the same group, is totally unimodular. The directed incidence matrix satisfies this with a single group, since each column already holds one entry of each sign."),
  body("Interval matrices, network matrices and the incidence matrices of bipartite graphs are the other standard families. Their presence in a model is a signal that the integrality requirement may be free."),

  h2("5.8  References"),
  body("Hoffman, A. J. and Kruskal, J. B., Integral boundary points of convex polyhedra, in Linear Inequalities and Related Systems, Annals of Mathematics Studies 38, Princeton University Press, 1956."),
  body("Ghouila-Houri, A., Caractérisation des matrices totalement unimodulaires, Comptes Rendus de l'Académie des Sciences, volume 254, 1962."),
  body("Schrijver, A., Theory of Linear and Integer Programming, Wiley, 1986, Chapters 19 and 20."),
  body("Nemhauser, G. L. and Wolsey, L. A., Integer and Combinatorial Optimization, Wiley, 1988, Part III."),
);

// ======================================================================
// APPENDIX
// ======================================================================
push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("Appendix A.  Group Practice 1: The Longest Path Problem"),
  body("Slide 35. In a directed graph, a team must travel from a starting location s to a destination t while visiting each location at most once and maximizing the total travel distance."),
  body("The sets and parameters are those of Section 2. The decision variables are the same binary arc variables. Two changes to the model are required, and the second is the one that matters."),
  eqL([mr("max  "), sum(`(i,j) ${IN} A`, [sub("c", "ij"), sub("x", "ij")])]),
  body("subject to"),
  eqL([sum(`j ${IN} ${DELTA}⁺(i)`, [sub("x", "ij")]), mr(" − "),
       sum(`j ${IN} ${DELTA}⁻(i)`, [sub("x", "ji")]), mr(" = "), sub("b", "i")],
      `for all i ${IN} V`),
  eqL([sum(`j ${IN} ${DELTA}⁺(i)`, [sub("x", "ij")]), mr(` ${LE} 1`)], `for all i ${IN} V`),
  eqL([sum(`{i,j} ${IN} A(S)`, [sub("x", "ij")]), mr(` ${LE} |S| − 1`)],
      `for all S ${SUBSET} V \\ {s, t}, |S| ${GE} 2`),
  eqL([sub("x", "ij"), mr(` ${IN} {0, 1}`)], `for all (i, j) ${IN} A`),
  gap(),
  body("The out-degree restriction enforces visiting each location at most once. The third family is subtour elimination, and it is not optional. Flow conservation together with the degree restriction still permits an s-to-t path accompanied by disjoint directed cycles elsewhere in the graph. Under minimization with nonnegative costs those cycles were harmless, since dropping them lowered the objective. Under maximization they are actively attractive, because every cycle adds length for free. Removing them requires the same exponential constraint family that appears in the travelling salesman problem."),
  body("The lesson is worth stating plainly. Shortest path and longest path differ by one word in the statement. Shortest path has a totally unimodular constraint matrix, a compact model and a polynomial algorithm. Longest path needs an exponential constraint family, loses total unimodularity, and is NP-hard. Changing a minimization to a maximization is not a cosmetic edit."),
);

// ======================================================================
const doc = new Document({
  creator: "Lidivine Kengne",
  title: "IE 5311 Part 1: Classic Problems and Formulations",
  styles: { default: { document: { run: { font: H.BODY, size: H.SZ, color: "000000" } } } },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 },
              margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2], buf);
  console.log("written", process.argv[2], buf.length, "bytes");
});
