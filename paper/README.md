# HyperVul — IEEE Conference Paper

`main.tex` is a self-contained IEEE conference paper (`IEEEtran`, `conference` option).

## Compiling on Overleaf
1. Create a new project and upload `main.tex` (or drag the whole `paper/` folder).
2. Set the compiler to **pdfLaTeX** (Menu → Settings → Compiler).
3. Compile. Overleaf runs the BibTeX/LaTeX passes automatically.

The bibliography is embedded inline via `thebibliography` (no separate `.bib` file
needed). All four figures are drawn with TikZ/pgfplots — no external image files
required. The two algorithms use the `algorithm`/`algorithmic` packages. All required
packages (`IEEEtran`, `pgfplots`, `algorithm`, `booktabs`, `listings`, `tikz`) ship
with Overleaf's default TeX Live, so no manual installation is needed.

## Status of the numbers
Result tables and the two case-study examples currently hold **placeholder values**
derived from `hypervul_fair_eval/IMPLEMENTATION_PLAN.md` (§10) and illustrative
patterns consistent with them. Replace these with the real 5-seed experimental outputs
before submission. The items to update:
- Table II   (`tab:rq1`)      — RQ1 generic baselines
- Table III  (`tab:rq2`)      — RQ2 representation ablation
- Table IV   (`tab:rq3`)      — RQ3 component ablation
- Table V    (`tab:perclass`) — per-class F1 breakdown *(needs new experiment)*
- Table VI   (`tab:fpr`)      — clean-corpus FPR
- Table VII  (`tab:eff`)      — params / train time / latency *(needs measurement)*
- Table VIII (`tab:sig`)      — significance tests
- Fig. 3 (`fig:pr`)           — PR-curve coordinates *(needs real curves)*
- Fig. 4 (`fig:loc`)          — localization case-study attributions *(needs real run)*
- §VII case-study prose       — the two walked-through contracts and their scores.

## Structure (8-page target)
Abstract · Introduction · Related Work (+positioning table) · Problem Formulation ·
Architecture (Alg. 1 construction, Alg. 2 thresholding, formalized localization &
contrastive loss) · Experimental Setup (+hyperparameter table) · Results (RQ1–RQ3,
per-class, FPR, sensitivity/PR curve, efficiency, significance) · Qualitative &
Localization Case Study · Threats to Validity · Discussion · Conclusion · References.
