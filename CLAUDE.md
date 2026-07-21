# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A SFBU CS570 group project (Team Vortex, Group 2) building an incremental movie-recommendation / rating-classification pipeline on the **MovieLens 1M** dataset using **PySpark**. All work lives in Jupyter notebooks, one per deliverable. There is no application, package, or test suite — the deliverables *are* the notebooks, and the graded artifact is the executed notebook with its cell outputs and written analysis.

- `Vortex_D1-D2.ipynb` — D1 (data loading + EDA) and D2 (cleaning + feature engineering).
- `Vortex_D3.ipynb` — D3 (linear classification: Logistic Regression pipeline, evaluation, interpretation).
- `SP26 CS570 Project - D*.{docx,pdf}` — the assignment specs. **Read the relevant D-spec before doing deliverable work** — it defines the exact required sections, questions, and grading structure the notebooks mirror.
- `ml-1m/` — raw dataset (`users.dat`, `ratings.dat`, `movies.dat`, `README`). Do not redistribute (see `ml-1m/README` license).

## Environment & running

- Requires **Java 17** (Temurin) for Spark. D3 hard-codes `JAVA_HOME = /Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home` — adjust for the local machine if Spark fails to start.
- Python **3.12** in a `.venv` (the D3 kernel is named `.venv`). `pyspark` and `pandas` are the core dependencies; there is no `requirements.txt`, so install PySpark into the venv manually.
- Spark runs **local mode** (`.master("local[*]")`) — no cluster. Everything executes on one machine.
- Run by opening the notebook in Jupyter (`jupyter lab`) with the `.venv` kernel selected, then Run All. Notebooks are meant to execute top-to-bottom in order; later cells depend on DataFrames built earlier.

## Data loading conventions

The `.dat` files are `::`-separated with **no header**. Every load uses an explicit `StructType` schema plus `.option("sep", "::")` — never rely on inferred schemas or default delimiters. Standard column names: `UserID, Gender, Age, Occupation, Zip-code` (users); `UserID, MovieID, Rating, Timestamp` (ratings); `MovieID, Title, Genres` (movies, `Genres` pipe-delimited).

## Pipeline architecture (the through-line across deliverables)

Each deliverable rebuilds on the previous one's logic, so the notebooks repeat the earlier steps rather than importing them:

1. **Load & join** — three DataFrames joined into `df_joined` on `UserID`/`MovieID`. `broadcast()` is used for the small dimension tables.
2. **Clean** — four canonical quality checks, each done as BEFORE → FIX → AFTER: duplicate `(UserID, MovieID)` ratings, referential integrity (users & movies), rating range (1–5), and a null audit.
3. **Feature engineering** — target is `high_rating` (binary, derived from `Rating`). Engineered predictors include `user_avg_rating`, `movie_avg_rating`, `movie_popularity`, `user_rating_count`, `gender_encoded`, `num_genres`, `release_year` (regex-extracted from `Title`), `movie_age`, and `primary_genre`.
4. **Model (D3)** — Spark ML `Pipeline(stages=[VectorAssembler, scaler, LogisticRegression])`, `randomSplit([0.8, 0.2], seed=42)`. Compared against a majority-class naive baseline; tuned with `CrossValidator` + `ParamGridBuilder` (regParam / elasticNetParam), evaluated with `areaUnderPR`. Interpretation reads `lr_model.coefficients` back against `feature_cols`.

When editing feature or cleaning logic, keep it consistent across **both** notebooks — D3 re-derives the D2 features, and divergence between them is a real source of bugs (see git history: "Fixed mismatched recall values", "Reran coefficients").

## Working conventions

- Keep `seed=42` and the `feature_cols` ordering stable — coefficient analysis and reported metrics are pinned to them.
- Preserve the spec-driven markdown section structure (numbered sections, BEFORE/FIX/AFTER cleaning blocks, the Contribution Statement at the end). Graders match against it.
- Each deliverable is developed on a branch and merged via PR (see git history). Match that flow.
- Commit executed notebooks with outputs intact — the outputs are part of the deliverable, not noise to strip.
