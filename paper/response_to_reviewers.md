# Response to Reviewers — IEEE OMLET 2026, Paper ID 528

**Title:** Leakage-Aware Intersectional Fairness Mitigation for Distributed Rating
Classification in Recommender Systems

We thank both reviewers for the careful reading and the constructive comments. The
decision was *accept with minor revision*. Below we address every comment and point
to the exact location of each change in the revised manuscript. All changes are
textual (framing, scope, and limitations); no results were altered.

---

## Reviewer 1

### R1.1 — "The paper lacks technical novelty as threshold calibration is standard."

We agree that threshold calibration is a standard post-processing tool and we do not
claim it as a new technique. We have made the actual contribution explicit and moved
it to the front of the paper.

- **Added** a new *"Scope and novelty"* paragraph immediately after the Contributions
  list (§I). It states that the contribution is the *combination* prior work leaves
  unaddressed — a leakage-aware fairness audit on a **distributed** rating pipeline,
  an **intersectional** calibration benchmarked head-to-head against single-attribute
  calibration **with paired significance tests**, and replication across an
  independent dataset and a second model class.
- This complements the existing Related Work text (§II, "We do not claim
  intersectional fairness as novel; rather, we *adapt* threshold calibration to the
  joint attribute cell …") and the positioning Table I, which shows no prior entry
  combining all four properties.

### R1.2 — "The evaluation relies on small public datasets with demographic information."

- **Revised** the *External validity* paragraph (§VIII) to note that MovieLens 1M and
  100K are the de-facto benchmarks for demographic fairness in recommendation
  (Ekstrand et al.), and that public rating datasets carrying self-reported gender
  and age are scarce because such attributes are seldom collected or released for
  privacy reasons. This constrains cross-domain evaluation for the subfield as a
  whole, and we now say so explicitly rather than treating it as a one-line caveat.
- The study already validates every headline result across eight random splits, a
  second independent dataset (§VII), and a second model class (gradient-boosted
  trees, §VII-A), which is the strongest form of external check available given the
  data landscape.

### R1.3 — "The intersectional calibration method fails to scale with multiple attributes."

We agree, and the manuscript already analyzes this explicitly.

- §VIII, *Scalability* paragraph: with `d` attributes of `k` levels the number of
  calibrated cells grows as `k^d`; beyond a few attributes per-cell samples shrink
  until quantile estimates become unstable. We explicitly state the results "should
  be read as evidence for *joint* over single-attribute post-processing at low
  attribute counts, **not as a claim of scalability to high-dimensional
  intersections**," and point to subgroup-fairness methods (Kearns et al.) as the
  direction for many attributes.
- §IX (Conclusion / Future Work) lists regularized or hierarchical intersectional
  thresholds for many fine-grained strata as the follow-up.

No change required; we note the scope was already bounded in the submitted version.

### R1.4 — "Target leakage correction yields only a negligible difference in performance."

This is correct on aggregate accuracy (0.723 → 0.719), and that is precisely the
point — the correction is not aimed at predictive gain. We have clarified this.

- **Revised** §I ("First, …"): the correction is necessary "not [for] predictive
  performance but [for] the integrity of the per-group fairness metrics computed
  afterward, since leaked targets contaminate the same selection rates the audit
  inspects."
- **Revised** §V, *Leakage correction*: leaked features embed the target in the
  input, so a fairness audit run on the leaky model reports per-group selection
  rates and disparity measures that are partly an evaluation artifact rather than a
  property of the model. Leakage here distorts the **fairness** reading, not the
  headline score.

### R1.5 — "The study audits binary rating prediction instead of recommendation ranking."

This is a deliberate scoping choice, now stated up front.

- **Added** to the new *Scope and novelty* paragraph (§I): we audit the
  rating-classification stage rather than top-`k` ranking because score bias at this
  stage propagates into any ranking built on it, so the classifier is where a
  disparity must first be measured and corrected.
- Existing text already frames this (§II, "we audit the upstream
  rating-classification stage, where disparities originate but are rarely measured")
  and §IX lists "extending the audit from rating classification to top-`k`
  recommendation" as future work.

---

## Reviewer 2

### R2.1 — "The leakage-aware evaluation is carefully designed and strengthens the credibility of the fairness analysis."

We thank the reviewer. The clarifications made for R1.4 further sharpen why the
leakage-aware design matters for the fairness reading specifically.

### R2.2 — "The findings are well validated across multiple random splits, a second dataset and another classifier."

We thank the reviewer; no change.

### R2.3 — "Generalization remains limited because both evaluation datasets are from the MovieLens domain."

We agree and have strengthened the acknowledgement.

- **Revised** §VIII *External validity* (same edit as R1.2): generalization to
  non-movie domains remains open; we now frame this as a subfield-wide constraint
  driven by the scarcity of demographically labeled public rating data, and we do
  not generalize beyond the audited setting without re-auditing.

---

## Summary of changes

| Location | Change |
|---|---|
| §I, after Contributions | New *"Scope and novelty"* paragraph (R1.1, R1.5) |
| §I, "First …" sentence | Reframed leakage correction around fairness-metric integrity (R1.4) |
| §V, *Leakage correction* | Added rationale: leakage distorts the fairness reading, not accuracy (R1.4) |
| §VIII, *External validity* | Benchmark justification + subfield-wide data-scarcity framing (R1.2, R2.3) |
| Back matter | *AI Use Disclosure* section added; *Reproducibility* wording tightened (camera-ready) |

No experimental results, tables, or figures were changed. The manuscript remains 6
pages.
