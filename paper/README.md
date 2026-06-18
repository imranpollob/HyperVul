# HyperVul — Paper Draft (ICTAI 2026)

Initial draft for **advisor feedback**. Official IEEE conference format (IEEEtran, two-column),
target **8 pages**.

## Build
- **Overleaf** (recommended): upload `main.tex` + `refs.bib`, set compiler to pdfLaTeX. IEEEtran
  is built in.
- **Local**: `latexmk -pdf main.tex` (needs `texlive` + IEEEtran). No LaTeX is installed in this
  repo's environment, so the PDF is not built here.

## Status — what is real vs. to-do
All numbers in the draft are **measured** from our runs:
- Table I (RQ1, representation): `experiments/results/representation_findings.md`.
- Tables II/III (RQ2, safety features + OOD FPR): `experiments/results/ablation_summary.md`
  (arms `Sym:none/security/full`, §2 and §4).
- Table IV (RQ3, rule baselines): `experiments/results/baseline_comparison_heuristics.md`.

Open items are flagged inline with `\todo{...}`. The big ones:
1. **Architecture figure** (`figures/overview.pdf`) — pipeline diagram.
2. **Dataset statistics table** (RQ-setup) — #projects/contracts/interactions/SWC dist.
3. **Cross- vs intra-contract table** (RQ4).
4. **References** — `refs.bib` entries are well-known works but **every entry must be verified**
   (venue/year/pages); several are marked `TODO: verify`, notably `dappscan`, `gnnscv`, `smartbert`.
5. **Author block / affiliations / reproducibility link.**
6. Future-work hooks already written into the text: full-benchmark scale-up, a learned external
   baseline on this split, and a localization faithfulness study.

## Framing (decisions taken — flag for advisor)
- Title leads with the **"when does structure help"** finding + **safety-aware features**, not a
  state-of-the-art F1 claim (we don't have one and shouldn't claim one).
- The **SCL calibration** is presented as an honest **negative result**, contrasted with the
  safety-feature win ("features beat loss tricks").
- The **localization head** is presented as an architectural capability; its quantitative
  evaluation is future work.
- Static-analyzer (Slither/Mythril) comparison is **absent by necessity** (contracts don't compile
  without unbundled deps) and framed as a motivation, not an omission.
