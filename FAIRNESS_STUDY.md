# Fairness Study (D4 extension) — MovieLens 1M

Extends the D3 Spark logistic-regression rating classifier into a **fairness audit and
mitigation** study, and writes it up as an IEEE conference paper targeting
**OMLET 2026** (IEEE Int. Conf. on Optics, Machine Learning and Emerging Technologies).

## What's here
- `fairness_study.py` — the full Spark pipeline: leakage fix, honest retrain, group
  fairness metrics (gender + age), and two mitigations. Writes `fairness_results.json`,
  `fairness_by_group.csv`.
- `make_figures.py` — renders the three paper figures from `fairness_results.json`.
- `paper/main.tex`, `paper/references.bib` — IEEEtran conference paper.
- `paper/main.pdf` — compiled paper (4 pages).
- `paper/fig_*.png` — figures.

## Key findings (all from real runs, seed 42)
| Result | Value |
|---|---|
| Leakage effect (accuracy) | 0.723 → **0.719** (modest) |
| Gender disparity | DPD 0.036, DI 0.95, EOD 0.007 (**mild**) |
| Age disparity | DPD 0.146, DI **0.80**, EOD 0.090 (**substantial**) |
| Feature removal on age | DPD 0.146 → **0.215** (worse — unawareness fails) |
| Per-group thresholds (gender) | DPD 0.036 → **0.001** at 0.0008 accuracy cost |

**Story:** aggregate accuracy (~0.72) hides an age bias that gender metrics don't show;
dropping protected attributes doesn't fix it (proxies remain); cheap per-group
thresholding fixes the *targeted* attribute only.

## Reproduce
Requires Java 17 and a Python 3.11 venv with PySpark. **Unset `SPARK_HOME`** if a
Homebrew Spark is installed, or the bundled Spark jars will clash.

```bash
python3.11 -m venv .venv && .venv/bin/pip install pyspark==3.5.3 pandas numpy matplotlib
env -u SPARK_HOME JAVA_HOME=/path/to/temurin-17 .venv/bin/python fairness_study.py
.venv/bin/python make_figures.py
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Honest caveats (also in the paper's Threats to Validity)
- Single split/seed; **no cross-seed variance or significance tests yet** — the top
  priority before submission.
- MovieLens gender is a self-reported binary; the audit can't speak to non-binary users.
- Per-group thresholding needs group membership at inference (a governance question).
