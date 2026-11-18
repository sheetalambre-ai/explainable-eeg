# Corrected Results Summary

Run date: 2026-11-13. Analysis uses the 296-EDF local raw archive and the leakage-conscious code in `src/corrected_experiments.py`. Main result tables are generated from these files; original outputs elsewhere under `results/` remain historical and are not corrected estimates.

## Primary cross-block identification

Closed-set 20-way balanced accuracy; chance is 5%. Confidence intervals bootstrap participants (5,000 resamples). The main logistic, power result has a 2,000-permutation participant-label test in each direction (minimum attainable p = 0.0005).

| Preprocessing / representation / model | Arabic → Hindi | Hindi → Arabic |
|---|---:|---:|
| Filtered, no ICA / power / logistic | 92.4% (86.5–96.7) | 93.5% (88.9–96.7) |
| Enrollment-only ICA / power / logistic | 92.8% (87.2–96.8), p=0.0005 | 93.7% (89.2–96.8), p=0.0005 |
| Enrollment-only ICA / power / shrinkage LDA | 89.5% (81.3–96.1) | 94.2% (89.5–97.7) |
| Enrollment-only ICA / power / linear SVM | 95.1% (91.8–97.7) | 94.6% (90.1–97.7) |
| Enrollment-only ICA / coherence / logistic | 95.0% (92.3–97.2) | 95.7% (91.0–98.5) |
| Enrollment-only ICA / power + coherence / logistic | 95.8% (92.9–98.0) | 96.2% (91.6–98.9) |

No test is reported for superiority between representations; intervals overlap. The accuracy of 4-s fused features is a point estimate, not evidence of a statistically reliable gain. Enrollment-only ICA excluded zero components in all 40 participant-direction fits. Thus the ICA comparison establishes leakage-safe fit scope, but not a benefit from ocular-component removal. No-ICA and ICA logistic power scores are very close.

## Evidence duration and enrollment cost

With enrollment-only ICA and power/logistic, test posterior aggregation gives:

| Test evidence | Arabic → Hindi | Hindi → Arabic |
|---:|---:|---:|
| 4 s | 92.8% | 93.7% |
| 8 s | 95.4% | 96.3% |
| 16 s | 96.4% | 96.8% |
| 32 s | 97.9% | 97.5% |

These are same-session estimates. The initial pooled duration CSV has no interval; participant-clustered CIs are supplied in `test_evidence_duration_clustered.csv`. In repeated enrollment subsampling, one 4-s window per identity yields 54.1% and 53.7%; 32 windows (128 s per identity) yields 89.2% and 92.0%; 64 windows (256 s) yields 91.7% and 93.3%. Enrollment curves reuse the full-block-selected logistic C and are descriptive rather than an optimized enrollment protocol.

## Artifact sensitivity

Under enrollment-only ICA, restricting features to 1–13 Hz at all channels yields 87.5% and 90.7%. Restricting further to six selected sites (F3/F4/P3/P4/O1/O2) yields 76.1% and 74.9%. Identity information remains above chance, but performance degrades. This does not prove neural specificity or eliminate EMG, eye, electrode-contact, and session artifacts.

## Validation scope and incomplete comparisons

- File-level three-fold validation and all scaling/model selection use enrollment data only; the held-out language block is tested once.
- Evaluated baselines are logistic regression, shrinkage LDA, and linear SVM for power; logistic regression for coherence and fusion.
- Nearest-centroid and Mahalanobis implementations were not included in the completed grid. The previous EEGNet scores inherited full-session ICA and are not included as corrected baselines. Random forest/deep-network comparisons under corrected preprocessing remain outstanding.
- Verification EER and open-set detection are omitted as operational results because the 20-person dataset cannot supply suitably independent enrollment, calibration, and final test identity cohorts.
- `leakage_audit.csv` contains 40 training-only ICA fits. `per_subject_metrics.csv`, `artifact_sensitivity.csv`, duration CSVs, and confusion matrices preserve the corresponding per-person detail.

## Reviewer-response analyses

- **Macro-F1:** enrollment-only ICA power/logistic macro-F1 is 92.2% (88.5–95.1) for Arabic→Hindi and 93.5% (90.7–95.7) for Hindi→Arabic. The complete model table is `participant_macro_metrics.csv`.
- **Native-language/nationality cohorts:** Arabic-native/Yemeni mean recall is 97.1% (95.4–98.5) and Hindi-native/Indian recall is 88.5% (78.5–96.2) in Arabic→Hindi. In Hindi→Arabic the means are 96.1% (93.6–98.0) and 91.3% (83.2–97.2). The cohort gap is descriptive because native language and nationality are fully confounded; sex is imbalanced across those same groups.
- **Sex groups:** Arabic→Hindi mean recall is 96.3% (93.9–98.3) in 12 male-coded participants and 87.5% (75.1–96.6) in eight female-coded participants. Hindi→Arabic is 93.1% (86.2–97.5) and 94.6% (90.9–98.1). Group intervals are wide and overlapping; these small data cannot isolate sex or nationality effects.
- **Individual stability:** per-person recall spans 50.0–100% for Arabic→Hindi and 59.2–100% for Hindi→Arabic. Two and one participants, respectively, are below 80% recall. Macro-F1 and all individual precision/recall/F1 are provided in `per_subject_metrics.csv`.
- **Paired contrasts:** paired participant bootstrap intervals and Wilcoxon tests compare six model/representation/preprocessing contrasts per direction. None survives Holm correction across the 12 tests (smallest adjusted p=0.0766). Thus the larger SVM/coherence/fusion point estimates do not establish a reliable ranking.
- **Matched full-session ICA diagnostic:** legacy features formed with ICA fit on both language blocks were re-evaluated using the same enrollment-only file-level classifier tuning. They yield 93.1% (87.5–97.2) and 94.6% (90.1–97.6), compared with 92.8% and 93.7% for enrollment-only ICA. Paired participant differences (enrollment-only minus full-session) are −0.3 and −0.9 percentage points, with Holm-adjusted p=0.685 and 0.578. Similar point estimates do not make test-distribution exposure methodologically safe; the corrected fit-scope remains the primary result.
- **Window dependence:** test-evidence duration intervals now bootstrap the 20 participant-level recalls after within-participant/file score aggregation. See `test_evidence_duration_clustered.csv` and the corresponding per-subject file. The primary 4-s window CI likewise resamples participants, not windows.
- **Confusion matrices:** direction-specific raw and row-normalized 20×20 matrices are available for the primary model, as well as the rendered two-panel `confusion_primary_directions.png`.

The group and paired analyses are exploratory. In particular, no cohort-stratified result is evidence of language invariance across nationalities or populations. A diverse independent cohort and counterbalanced/repeated-session data are still required.
