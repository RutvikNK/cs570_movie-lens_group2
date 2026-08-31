# Revision Notes — IEEE OMLET 2026, Paper ID 528

**Title:** Leakage-Aware Intersectional Fairness Mitigation for Distributed Rating
Classification in Recommender Systems
**Decision:** Accept with Minor Revision
**This file:** at-a-glance record of how every reviewer comment was addressed and
what was changed for camera-ready. Full prose response: `response_to_reviewers.pdf`.

---

## 1. Are all reviewer comments addressed?

**Yes — all 8 (Reviewer 1: 5 comments; Reviewer 2: 3).** Every change is textual
(framing, scope, limitations). No experiments, tables, figures, or numbers were
altered. Line numbers below refer to `main_camera_ready.tex`.

| # | Reviewer comment | How it was addressed | Location |
|---|---|---|---|
| **R1.1** | Lacks technical novelty — threshold calibration is standard | Added a *"Scope and novelty"* paragraph: explicitly concedes calibration is not new; states the contribution is the **combination** prior work leaves unaddressed — leakage-aware audit + distributed pipeline + intersectional-vs-single calibration with paired significance tests + cross-dataset/model replication. Reinforced by Related Work ("We do not claim intersectional fairness as novel…") and positioning Table I. | §I L131; §II L173, L179; Table I |
| **R1.2** | Evaluation relies on small public datasets with demographics | Reworked *External validity*: MovieLens 1M/100K are the de-facto demographic-fairness benchmarks (Ekstrand et al.); demographically labeled public rating data is scarce for privacy reasons — a constraint on the **whole subfield**, now stated explicitly rather than as a one-line caveat. | §VIII L537–L543 |
| **R1.3** | Intersectional calibration does not scale with many attributes | Already handled by the *Scalability* paragraph: `k^d` cell growth with `d` attributes of `k` levels; per-cell samples shrink until quantile estimates destabilize; explicit statement that results are evidence for **joint over single-attribute** post-processing at low attribute counts, **not a claim of scalability** to high-dimensional intersections. | §VIII L524–L535 |
| **R1.4** | Leakage correction yields only a negligible performance difference | Reframed in two places: the correction is not about accuracy (0.723→0.719) but about **fairness-metric integrity** — leaked targets contaminate the per-group selection rates the audit inspects, so a leaky model's disparity numbers are partly an evaluation artifact. | §I L92–L95; §V L288–L293 |
| **R1.5** | Audits binary rating prediction, not recommendation ranking | Stated in the *Scope and novelty* paragraph as a deliberate choice: score bias at the rating-classification stage propagates into any ranking built on it, so the classifier is where disparity must first be measured and corrected; the ranking-level audit is future work (also in §IX). | §I L137–L140; §IX |
| **R2.1** | (Positive) Leakage-aware evaluation strengthens credibility | No change required. The R1.4 edits further sharpen why the leakage-aware design matters for the fairness reading specifically. | — |
| **R2.2** | (Positive) Findings validated across splits, a second dataset, another classifier | No change required. | — |
| **R2.3** | Generalization limited — both datasets are MovieLens | Same *External validity* edit as R1.2: the MovieLens-only scope is explicitly conceded and framed as a subfield-wide data-availability constraint; results are not generalized without re-auditing. | §VIII L537–L543 |

---

## 2. Camera-ready formatting changes (OMLET guidelines)

Source: <https://ieeeomlet.org/camera-ready> and the OMLET LaTeX template.

| Requirement | Change made |
|---|---|
| De-anonymize | Double-blind block → real author block (name, department, institution, city, email); no honorific titles. `main_camera_ready.tex` holds the de-anonymized version; `main_anon.tex` keeps the review version. |
| First-page header | Added via `fancyhdr`: `2026 IEEE International Conference on Optics, Machine Learning and Emerging Technology (OMLET) / 29–31 October 2026, Nairobi, Kenya`. |
| First-page footer | Added: `979-8-3195-1287-1/26/$31.00 ©2026 IEEE` (IEEE copyright/ISBN line, required for Xplore). |
| "No bold text" | All author-added `\textbf{…}` run-in headings → `\textit{…}`; Table II best-DPD cells `\mathbf{…}` → `\underline{…}` with caption updated ("…per attribute is underlined"). Abstract left in the IEEEtran class default (bold by the class, present in OMLET's own template — not author-added). No `\color`/`\textcolor` anywhere. |
| "No extra files" in the paper | The response-to-reviewers letter is a separate deliverable, not bundled into the camera-ready PDF. |
| Page limit 4–6 | Paper is 6 pages. |
| Template | OMLET's LaTeX template is stock `IEEEtran` conference class; `IEEEtran.cls` bundled in the source zip. |
| Submission bundle | `528.zip` = `528_Camera ready.pdf` + `528_Source File.zip` (tex, bib, bbl, cls, 5 figures). Source zip verified to compile standalone to 6 pages. |

---

## 2b. Second-pass polish (internal review before upload)

Seven wording/technical corrections made after a line-by-line check of the
camera-ready PDF against the reviewer comments. Applied to both `.tex` files;
still 6 pages.

| # | Issue | Fix |
|---|---|---|
| 1 | Conclusion said "We **introduced** intersectional threshold calibration", contradicting the §I novelty disclaimer | → "We **adapted** threshold calibration to intersectional gender×age groups" |
| 2 | §VII rendered `p_{\text{age}}=2×10⁻⁶` as "page = 2 × 10⁻⁶" on copy | → bare `p = 2×10⁻⁶ for age`, matching the rest of §VII |
| 3 | Post-processing thresholds are estimated on the **same test split** used to report fairness (confirmed in `Vortex_D4_Fairness.ipynb`: `threshold_pred(base_pred, …)` takes quantiles of the test-set scores) — not previously disclosed | Added an honest statement in §III-F ("estimated on the same test split … so the mitigation figures are a best case") and a limitation in §VIII Internal validity ("optimistic; a split-then-freeze protocol is left to future work"). **Not** claimed as train/validation-fit, because it isn't. |
| 4 | "independent second dataset" / "independent collection" overstated vs. R2.3 | → "separately collected MovieLens 100K dataset" throughout (abstract, contributions, §I, §VII, §VIII) |
| 5 | "score bias … propagates into **any** ranking" was too absolute | → "score disparities … **can propagate into** rankings built from these scores" |
| 6 | §VIII said "all directional effects are significant at p<10⁻⁹" — that is the t-test; Table V Wilcoxon p-values are 0.004 | → "significant under the paired t-tests (p<10⁻⁹) and corroborated by the Wilcoxon signed-rank tests (p=0.004, the smallest value attainable at n=8)" |
| 7 | §I "releasing a reproducible Spark **notebook**" vs. §Reproducibility "available upon request" | → §I "a single reproducible Spark **implementation**"; §Reproducibility unchanged (available on request) |

Item 3 is the substantive one: it converts a latent methodological weakness (evaluation-set threshold tuning) into a disclosed limitation with a concrete future-work protocol.

---

## 3. Submission checklist

Done:
- [x] All reviewer comments incorporated (§1 above)
- [x] Manuscript de-anonymized
- [x] OMLET header + IEEE copyright footer
- [x] No author-added bold / no colored fonts
- [x] 6 pages, clean build, no undefined references
- [x] `528.zip` assembled to the required name/structure
- [x] `response_to_reviewers.pdf` prepared for the TPC

Pending (author actions, deadline **September 10, 2026**):
- [ ] Validate the PDF with **IEEE PDF eXpress** — Conference ID `69676X` — and put the certified PDF into `528.zip` as `528_Camera ready.pdf`
- [ ] Similarity check: overall < 25% (incl. bibliography), single source < 4%
- [ ] Complete and sign the **eCopyright form** via the MyProConf Author Portal
- [ ] Upload `528.zip` under *Camera-Ready Submission* (as Contact Author)
- [ ] Register at least one author

---

## 4. Git trace

All merged into `RutvikNK/cs570_movie-lens_group2` `main`:

| Commit | What |
|---|---|
| `fafa8db` | AI Use Disclosure section + Reproducibility reworded |
| `28c29c9` | Reviewer-comment revisions (text) |
| `859aafe` | Fix section cross-references in response letter |
| `35a2388` | De-anonymized camera-ready + submission package |
| `0c8bc28` | OMLET first-page header/footer + `528.zip` |
| `9960cde` | Remove author-added bold text |
| `7aec0b1` | Merge PR #12 |
| `ef51c62` | Merge PR #13 |
| `ab9b395` | Add REVISION_NOTES.md (merged in PR #14) |
| _(PR #15)_ | Second-pass polish: 7 reviewer-alignment fixes (§2b) |
