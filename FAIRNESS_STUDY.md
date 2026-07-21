# Fairness Study (D4 extension) — MovieLens 1M

Extends the D3 Spark logistic-regression rating classifier into a **fairness audit,
a new mitigation method, and a cross-seed significance study**, written up as an IEEE
conference paper targeting **OMLET 2026** (IEEE Int. Conf. on Optics, Machine Learning
and Emerging Technologies).

## What's here
- `Vortex_D4_Fairness.ipynb` — the full study as an executed Spark notebook: leakage fix,
  group fairness metrics (gender + age), four mitigations, and an **8-seed significance
  test**. Writes `fairness_results_d4.json`, `fairness_cross_seed.csv`, and the figures.
- `fairness_study.py` — the earlier single-seed script version (kept for reference).
- `paper/main.tex`, `paper/references.bib` — IEEEtran conference paper (5 pages).
- `paper/main.pdf` — compiled paper.
- `paper/fig_*.png` — figures (age skew, multi-attribute DPD, cross-seed boxplot, tradeoff).

## Key findings (all from real runs; mean ± std over 8 seeds)
| Result | Value |
|---|---|
| Leakage effect (accuracy) | 0.7220 → **0.7178** (modest, every seed) |
| Gender disparity (baseline) | DPD 0.038 ± 0.002, DI 0.94 (**mild**) |
| Age disparity (baseline) | DPD 0.145 ± 0.005, DI **0.80** (**substantial**) |
| Feature removal on age | DPD 0.145 → **0.213** (worse; H3 *p*=1.8e−11) |
| Gender-only threshold on age | DPD 0.145 → 0.145 (**no transfer**; H4 *p*=0.94) |
| Intersectional threshold (gender) | DPD 0.038 → **0.001** (H1 *p*=3.4e−10) |
| Intersectional threshold (age) | DPD 0.145 → **0.003** (H2 *p*=1.7e−12) |
| Intersectional accuracy cost | 0.7178 → 0.7157 (**0.21 pp**) |

**Story:** aggregate accuracy (~0.72) hides an age bias that gender metrics don't show;
dropping protected attributes makes age *worse* (proxies remain); single-attribute
thresholding fixes only the attribute it targets; **intersectional (gender×age)
thresholding closes both gaps at once** for a small accuracy cost. Every headline claim
is validated across 8 seeds with paired *t*- and Wilcoxon tests.

## Reproduce
Requires Java 17 and a Python 3.11 venv with PySpark + scipy. **Unset `SPARK_HOME`** if a
Homebrew Spark is installed, or the bundled Spark jars will clash.

```bash
python3.11 -m venv .venv
.venv/bin/pip install pyspark==3.5.3 pandas numpy matplotlib scipy jupyter nbconvert
env -u SPARK_HOME -u PYSPARK_SUBMIT_ARGS JAVA_HOME=/path/to/temurin-17 \
  .venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=2400 Vortex_D4_Fairness.ipynb
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Honest caveats (also in the paper's Threats to Validity)
- Cross-seed significance is now done (8 seeds); std ≤ 0.005 DPD, all directional effects
  significant at *p* < 1e−9.
- Intersectional calibration estimates thresholds on smaller strata (14 gender×age cells,
  smallest ~5,400 test rows); it may need smoothing/regularization for many fine-grained
  attributes.
- MovieLens gender is a self-reported binary; the audit can't speak to non-binary users.
- Per-group thresholding needs group membership at inference (a governance question).
