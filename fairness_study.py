"""
Fairness audit and mitigation of demographic bias in distributed rating
classification on MovieLens 1M (Spark ML).

This extends the D3 Logistic Regression pipeline with:
  (1) a target-leakage fix (user/movie averages computed on TRAIN only),
  (2) group fairness metrics across Gender and Age (DPD, EOD, DI, per-group acc),
  (3) two mitigations: sensitive-feature removal and per-group thresholding,
  (4) a fairness-accuracy tradeoff summary + figure.

Run:  <venv>/bin/python fairness_study.py
Outputs: fairness_results.json, fairness_by_group.csv, fairness_tradeoff.png
"""
import os
import sys
import json

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
os.environ.setdefault(
    "JAVA_HOME", "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home"
)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, IntegerType, StringType,
)
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.functions import vector_to_array

SEED = 42
DATA = "./ml-1m"

spark = (
    SparkSession.builder.appName("MovieLens Fairness Study")
    .master("local[*]")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")


# --------------------------------------------------------------------------
# 1. Load
# --------------------------------------------------------------------------
def load():
    users_schema = StructType([
        StructField("UserID", IntegerType()), StructField("Gender", StringType()),
        StructField("Age", IntegerType()), StructField("Occupation", IntegerType()),
        StructField("Zip", StringType()),
    ])
    ratings_schema = StructType([
        StructField("UserID", IntegerType()), StructField("MovieID", IntegerType()),
        StructField("Rating", IntegerType()), StructField("Timestamp", IntegerType()),
    ])
    movies_schema = StructType([
        StructField("MovieID", IntegerType()), StructField("Title", StringType()),
        StructField("Genres", StringType()),
    ])
    opt = dict(sep="::", header="false", quote='"', escape='"', multiLine="true")
    users = spark.read.options(**opt).schema(users_schema).csv(f"{DATA}/users.dat")
    ratings = spark.read.options(**opt).schema(ratings_schema).csv(f"{DATA}/ratings.dat")
    movies = spark.read.options(**opt).schema(movies_schema).csv(f"{DATA}/movies.dat")
    return users, ratings, movies


users, ratings, movies = load()

# Clean: drop duplicate (UserID, MovieID), keep valid ratings, referential integrity
ratings = ratings.dropDuplicates(["UserID", "MovieID"])
ratings = ratings.filter((F.col("Rating") >= 1) & (F.col("Rating") <= 5))
ratings = ratings.join(users.select("UserID"), "UserID", "inner")
ratings = ratings.join(movies.select("MovieID"), "MovieID", "inner")

# Movie-level static features (not label-dependent): release_year, num_genres
movies = movies.withColumn(
    "release_year",
    F.regexp_extract("Title", r"\((\d{4})\)", 1).cast(IntegerType()),
).withColumn(
    "num_genres", F.size(F.split("Genres", r"\|"))
).withColumn(
    "movie_age", F.lit(2000) - F.col("release_year")
)

df = (
    ratings
    .join(users, "UserID")
    .join(movies.select("MovieID", "release_year", "num_genres", "movie_age"), "MovieID")
    .withColumn("high_rating", (F.col("Rating") >= 4).cast(IntegerType()))
    .withColumn("gender_encoded", (F.col("Gender") == "F").cast(IntegerType()))
)

# --------------------------------------------------------------------------
# 2. Split FIRST, then engineer leakage-prone features on TRAIN only
# --------------------------------------------------------------------------
train, test = df.randomSplit([0.8, 0.2], seed=SEED)


def add_train_derived_features(train_df, test_df):
    """Compute user/movie averages and counts on TRAIN, map onto both splits.
    Unseen users/movies in test fall back to the global train mean."""
    global_mean = train_df.select(F.avg("Rating")).first()[0]

    user_avg = train_df.groupBy("UserID").agg(
        F.avg("Rating").alias("user_avg_rating"),
        F.count("*").alias("user_rating_count"),
    )
    movie_avg = train_df.groupBy("MovieID").agg(
        F.avg("Rating").alias("movie_avg_rating"),
        F.count("*").alias("movie_popularity"),
    )

    def attach(d):
        d = d.join(user_avg, "UserID", "left").join(movie_avg, "MovieID", "left")
        return d.fillna({
            "user_avg_rating": global_mean, "movie_avg_rating": global_mean,
            "user_rating_count": 0, "movie_popularity": 0,
        })

    return attach(train_df), attach(test_df), global_mean


train_fx, test_fx, global_mean = add_train_derived_features(train, test)


# Also build a LEAKY version (averages over full data) to quantify inflation
def add_leaky_features(full_df):
    user_avg = full_df.groupBy("UserID").agg(
        F.avg("Rating").alias("user_avg_rating"),
        F.count("*").alias("user_rating_count"),
    )
    movie_avg = full_df.groupBy("MovieID").agg(
        F.avg("Rating").alias("movie_avg_rating"),
        F.count("*").alias("movie_popularity"),
    )
    return full_df.join(user_avg, "UserID").join(movie_avg, "MovieID")


leaky = add_leaky_features(df)
leaky_train = leaky.join(train.select("UserID", "MovieID"), ["UserID", "MovieID"])
leaky_test = leaky.join(test.select("UserID", "MovieID"), ["UserID", "MovieID"])

BASE_FEATURES = [
    "Age", "Occupation", "user_avg_rating", "movie_avg_rating",
    "movie_popularity", "user_rating_count", "gender_encoded",
    "num_genres", "release_year", "movie_age",
]


# --------------------------------------------------------------------------
# 3. Train / evaluate helpers
# --------------------------------------------------------------------------
def train_lr(train_df, feature_cols):
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="raw_features",
                                handleInvalid="skip")
    scaler = StandardScaler(inputCol="raw_features", outputCol="features")
    lr = LogisticRegression(featuresCol="features", labelCol="high_rating", maxIter=100)
    model = Pipeline(stages=[assembler, scaler, lr]).fit(train_df)
    return model


def score(model, test_df, threshold=0.5):
    pred = model.transform(test_df).withColumn(
        "p1", vector_to_array("probability")[1]
    ).withColumn("pred", (F.col("p1") >= threshold).cast("double"))
    return pred


def overall_metrics(pred):
    tp = pred.filter("high_rating=1 AND pred=1.0").count()
    fp = pred.filter("high_rating=0 AND pred=1.0").count()
    tn = pred.filter("high_rating=0 AND pred=0.0").count()
    fn = pred.filter("high_rating=1 AND pred=0.0").count()
    n = tp + fp + tn + fn
    acc = (tp + tn) / n if n else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return dict(accuracy=acc, precision=prec, recall=rec, f1=f1,
               tp=tp, fp=fp, tn=tn, fn=fn, n=n)


def group_fairness(pred, group_col):
    """Per-group selection rate, TPR, FPR, accuracy → DPD, EOD, DI."""
    rows = (
        pred.groupBy(group_col).agg(
            F.count("*").alias("n"),
            F.avg("pred").alias("selection_rate"),
            F.avg(F.when(F.col("high_rating") == 1, F.col("pred"))).alias("tpr"),
            F.avg(F.when(F.col("high_rating") == 0, F.col("pred"))).alias("fpr"),
            F.avg((F.col("pred") == F.col("high_rating")).cast("double")).alias("accuracy"),
        ).orderBy(group_col).collect()
    )
    groups = {}
    for r in rows:
        groups[str(r[group_col])] = dict(
            n=r["n"], selection_rate=r["selection_rate"], tpr=r["tpr"],
            fpr=r["fpr"], accuracy=r["accuracy"],
        )
    srs = [v["selection_rate"] for v in groups.values() if v["selection_rate"] is not None]
    tprs = [v["tpr"] for v in groups.values() if v["tpr"] is not None]
    fprs = [v["fpr"] for v in groups.values() if v["fpr"] is not None]
    summary = dict(
        demographic_parity_diff=max(srs) - min(srs) if srs else None,
        disparate_impact=min(srs) / max(srs) if srs and max(srs) else None,
        equal_opportunity_diff=max(tprs) - min(tprs) if tprs else None,
        equalized_odds_fpr_diff=max(fprs) - min(fprs) if fprs else None,
    )
    return dict(groups=groups, summary=summary)


results = {"meta": {"seed": SEED, "global_train_mean": global_mean,
                    "train_n": train.count(), "test_n": test.count()}}

# --------------------------------------------------------------------------
# 4a. LEAKY model (reproduce the inflated D3-style numbers)
# --------------------------------------------------------------------------
print("Training LEAKY model (reproduces D3-style leakage)...")
leaky_model = train_lr(leaky_train, BASE_FEATURES)
leaky_pred = score(leaky_model, leaky_test)
results["leaky_model"] = overall_metrics(leaky_pred)
print("  leaky:", results["leaky_model"]["accuracy"], results["leaky_model"]["f1"])

# --------------------------------------------------------------------------
# 4b. HONEST baseline (leakage fixed)
# --------------------------------------------------------------------------
print("Training HONEST baseline (leakage fixed)...")
base_model = train_lr(train_fx, BASE_FEATURES)
base_pred = score(base_model, test_fx).cache()
results["honest_baseline"] = overall_metrics(base_pred)
results["honest_baseline"]["fairness_gender"] = group_fairness(base_pred, "Gender")
results["honest_baseline"]["fairness_age"] = group_fairness(base_pred, "Age")
print("  honest:", results["honest_baseline"]["accuracy"], results["honest_baseline"]["f1"])

# --------------------------------------------------------------------------
# 5a. Mitigation: sensitive-feature removal (drop gender + age)
# --------------------------------------------------------------------------
print("Mitigation 1: sensitive-feature removal...")
FAIR_FEATURES = [c for c in BASE_FEATURES if c not in ("gender_encoded", "Age")]
fr_model = train_lr(train_fx, FAIR_FEATURES)
fr_pred = score(fr_model, test_fx).cache()
results["mitigation_feature_removal"] = overall_metrics(fr_pred)
results["mitigation_feature_removal"]["fairness_gender"] = group_fairness(fr_pred, "Gender")
results["mitigation_feature_removal"]["fairness_age"] = group_fairness(fr_pred, "Age")

# --------------------------------------------------------------------------
# 5b. Mitigation: per-group thresholds to equalize selection rate (demographic parity)
# --------------------------------------------------------------------------
print("Mitigation 2: per-group thresholds (demographic parity post-processing)...")
# target selection rate = overall positive prediction rate of honest baseline
target_rate = base_pred.select(F.avg("pred")).first()[0]


def per_group_threshold_pred(pred, group_col, target):
    """For each group choose the threshold on p1 whose selection rate ~ target."""
    # approximate group thresholds via quantiles of p1 within each group
    thresholds = {}
    for g in [r[group_col] for r in pred.select(group_col).distinct().collect()]:
        sub = pred.filter(F.col(group_col) == g)
        # threshold = (1 - target) quantile of p1 → fraction >= t ≈ target
        q = sub.approxQuantile("p1", [1 - target], 0.01)
        thresholds[str(g)] = q[0] if q else 0.5
    mapping = F.create_map(*sum(([F.lit(k), F.lit(v)] for k, v in thresholds.items()), []))
    adj = pred.withColumn("gt", mapping[F.col(group_col).cast("string")]) \
              .withColumn("pred", (F.col("p1") >= F.col("gt")).cast("double"))
    return adj, thresholds


pg_pred, pg_thresholds = per_group_threshold_pred(base_pred, "Gender", target_rate)
pg_pred = pg_pred.cache()
results["mitigation_per_group_threshold"] = overall_metrics(pg_pred)
results["mitigation_per_group_threshold"]["thresholds"] = pg_thresholds
results["mitigation_per_group_threshold"]["fairness_gender"] = group_fairness(pg_pred, "Gender")
results["mitigation_per_group_threshold"]["fairness_age"] = group_fairness(pg_pred, "Age")

# --------------------------------------------------------------------------
# 6. Save
# --------------------------------------------------------------------------
with open("fairness_results.json", "w") as f:
    json.dump(results, f, indent=2)

# CSV of per-gender fairness across configs
import csv
with open("fairness_by_group.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["config", "gender", "n", "selection_rate", "tpr", "fpr", "accuracy"])
    for cfg in ["honest_baseline", "mitigation_feature_removal", "mitigation_per_group_threshold"]:
        for g, v in results[cfg]["fairness_gender"]["groups"].items():
            w.writerow([cfg, g, v["n"], v["selection_rate"], v["tpr"], v["fpr"], v["accuracy"]])

# Tradeoff figure: accuracy vs demographic parity difference (gender)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

configs = [
    ("Honest baseline", "honest_baseline"),
    ("Feature removal", "mitigation_feature_removal"),
    ("Per-group thresh.", "mitigation_per_group_threshold"),
]
xs = [results[c]["fairness_gender"]["summary"]["demographic_parity_diff"] for _, c in configs]
ys = [results[c]["accuracy"] for _, c in configs]
plt.figure(figsize=(5, 4))
plt.scatter(xs, ys, s=80)
for (label, _), x, y in zip(configs, xs, ys):
    plt.annotate(label, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=8)
plt.xlabel("Demographic Parity Difference (Gender) — lower is fairer")
plt.ylabel("Overall Accuracy")
plt.title("Fairness–Accuracy Tradeoff")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("fairness_tradeoff.png", dpi=200)

print("\n=== DONE ===")
print(json.dumps({k: (v if k == "meta" else results[k].get("accuracy"))
                  for k, v in results.items()}, indent=2))
spark.stop()
