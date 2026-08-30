"""Generate paper figures from fairness_results.json (no Spark needed)."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = json.load(open("fairness_results.json"))
configs = [
    ("Baseline", "honest_baseline"),
    ("Feature\nremoval", "mitigation_feature_removal"),
    ("Per-group\nthresholds", "mitigation_per_group_threshold"),
]
labels = [c[0] for c in configs]
gender_dpd = [R[c[1]]["fairness_gender"]["summary"]["demographic_parity_diff"] for c in configs]
age_dpd = [R[c[1]]["fairness_age"]["summary"]["demographic_parity_diff"] for c in configs]
acc = [R[c[1]]["accuracy"] for c in configs]

# Figure 1: DPD by protected attribute across configs (the main story)
x = np.arange(len(labels))
w = 0.35
fig, ax1 = plt.subplots(figsize=(5.2, 3.4))
b1 = ax1.bar(x - w/2, gender_dpd, w, label="Gender DPD", color="#4C72B0")
b2 = ax1.bar(x + w/2, age_dpd, w, label="Age DPD", color="#DD8452")
ax1.axhline(0.0, color="k", lw=0.5)
ax1.set_ylabel("Demographic Parity Difference\n(lower is fairer)")
ax1.set_xticks(x)
ax1.set_xticklabels(labels)
ax1.set_title("Demographic parity gaps across configurations")
ax1.legend(loc="upper left", fontsize=8)
for b in list(b1) + list(b2):
    ax1.annotate(f"{b.get_height():.3f}", (b.get_x() + b.get_width()/2, b.get_height()),
                 ha="center", va="bottom", fontsize=7)
plt.tight_layout()
plt.savefig("paper/fig_dpd.png", dpi=220)
plt.close()

# Figure 2: fairness-accuracy tradeoff (gender), annotated
fig, ax = plt.subplots(figsize=(5.2, 3.4))
sc = ax.scatter(gender_dpd, acc, s=90, c=["#4C72B0", "#DD8452", "#55A868"], zorder=3)
for lbl, gx, gy in zip([c[0].replace("\n", " ") for c in configs], gender_dpd, acc):
    ax.annotate(lbl, (gx, gy), textcoords="offset points", xytext=(6, 5), fontsize=8)
ax.set_xlabel("Gender Demographic Parity Difference (lower is fairer)")
ax.set_ylabel("Overall Accuracy")
ax.set_title("Fairness–accuracy tradeoff (gender)")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("paper/fig_tradeoff.png", dpi=220)
plt.close()

# Figure 3: selection rate by age band (baseline), shows the age skew
ages = ["1", "18", "25", "35", "45", "50", "56"]
sr = [R["honest_baseline"]["fairness_age"]["groups"][a]["selection_rate"] for a in ages]
fig, ax = plt.subplots(figsize=(5.2, 3.0))
ax.plot(range(len(ages)), sr, "o-", color="#DD8452")
ax.set_xticks(range(len(ages)))
ax.set_xticklabels([f"{a}" for a in ages])
ax.set_xlabel("MovieLens age band (youngest → oldest)")
ax.set_ylabel("Selection rate\nP(ŷ=1)")
ax.set_title("Baseline selection rate rises with user age")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("paper/fig_age.png", dpi=220)
plt.close()

print("wrote paper/fig_dpd.png, paper/fig_tradeoff.png, paper/fig_age.png")
