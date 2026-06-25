# HyperVul — IEEE Conference Paper

`main.tex` is a self-contained IEEE conference paper (`IEEEtran`, `conference` option).

## Compiling on Overleaf
1. Create a new project and upload `main.tex` (or drag the whole `paper/` folder).
2. Set the compiler to **pdfLaTeX** (Menu → Settings → Compiler).
3. Compile. Overleaf runs the BibTeX/LaTeX passes automatically.

The bibliography is embedded inline via `thebibliography` (no separate `.bib` file
needed). The two figures are drawn with TikZ — no external image files required.

## Status of the numbers
All result tables currently hold the **placeholder values from
`hypervul_fair_eval/IMPLEMENTATION_PLAN.md`** (Tables in §10 of that plan). Replace
them with the real 5-seed experimental outputs before submission. The numbers to
update live in:
- Table II  (`tab:rq1`)  — RQ1 generic baselines
- Table III (`tab:rq2`)  — RQ2 representation ablation
- Table IV  (`tab:rq3`)  — RQ3 component ablation
- Table V   (`tab:fpr`)  — clean-corpus FPR
- Table VI  (`tab:sig`)  — significance tests
- The inline figures in §VI text that quote deltas/$p$-values.

## Structure
8-page target. Section layout follows the approved plan:
Abstract · Introduction · Related Work · Problem Formulation · Architecture ·
Experimental Setup · Results · Discussion · Conclusion · References.
