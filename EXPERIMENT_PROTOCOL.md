# Corrected Experiment Protocol

> **Superseded (2026-11-21).** This document was written under the withdrawn "cross-script EEG identity recognition during reading" framing. The task may have been overt speech, identity is confounded with a single recording session, and script is confounded with time. See the status notice in `README.md`.

Status: complete for the evaluated comparison grid as of 2026-11-13. See `results/corrected/RESULTS_SUMMARY.md` and the CSV outputs. The completed grid evaluates logistic regression, shrinkage LDA and linear SVM for power, plus logistic regression for coherence and fused features.

## Dataset and task

- Source used: the 296-EDF `EEG RAW Dataset.zip` included in this project package. `dataset_manifest.csv` records subject, language, chunk, chronology, file size, CRC32, and the archive match.
- Analysis units: non-overlapping 4-s windows, 14 common scalp channels, 256 Hz. Welch PSD uses 2-s segments; features are 5 band log-power and relative-power values per channel (140 features). Coherence uses 91 channel pairs and five bands (455 features).
- Closed-set identity task: one full language block per participant is enrollment/training; the other language block is held out for testing. Run Arabic→Hindi and Hindi→Arabic separately.
- Language order is Arabic then Hindi for every participant in the local EDF headers. Transfer results are cross-block and cross-time; they are not a causal estimate of a language effect.

## Signal processing

1. Load each subject-language block separately and retain the same fixed channel order.
2. Apply 50/100-Hz notch, 1–45-Hz band-pass, and common-average reference separately by block.
3. Primary comparison: fixed filtering/reference without ICA.
4. ICA sensitivity: fit FastICA (99% variance criterion) using only the participant's enrollment language block. Detect ocular-correlated components using FP1/FP2 from that enrollment block only. Freeze the fitted ICA and exclusion list, then apply it to both the enrollment and test data. No ICA fitting or component selection uses the test block.
5. Record fit language, sample counts, component count/exclusions, and channel order in `results/corrected/leakage_audit.csv`.
6. Cut each EDF at its own boundaries; discard incomplete final 4-s windows. Do not concatenate windows across EDF boundaries.

## Models and representation comparisons

- Logistic regression, shrinkage LDA, and linear SVM for power; logistic regression for coherence and fused power+coherence.
- Representations: spectral power, band-averaged magnitude-squared coherence, and power + coherence.
- For each transfer direction and representation, choose hyperparameters from 3-fold file-level validation confined to the enrollment language. File folds are assigned cyclically within participant so every identity occurs in each validation fold and the fit portion.
- StandardScaler is fitted within each model fit fold using training samples only. The final model is refitted on all enrollment windows with the selected parameter and evaluated once on the held-out language block.
- Random seed is fixed at 42. Classifier comparisons use the same windows, files, channels and direction.

## Outcomes and uncertainty

- Primary outcome: 20-way balanced accuracy (mean participant recall), reported separately for each transfer direction.
- Participant-level precision, recall and F1; per-participant confusion matrices; participant bootstrap 95% percentile CIs (5,000 resamples for the primary run; 10,000 resamples for the supplementary cohort/paired summaries).
- Cohort-stratified summaries for native-language/nationality cohort and sex, with participants as the resampling unit; native language and nationality are confounded in this dataset and are not causally separable.
- Paired participant recall contrasts with paired bootstrap CIs and Wilcoxon signed-rank tests; Holm adjustment across 12 model/preprocessing comparisons.
- For the predeclared primary ICA + power + logistic result, a Monte Carlo permutation test shuffles the mapping from held-out participant labels to enrolled identity classes (2,000 permutations), keeping every participant's windows together.
- Enrollment duration is estimated separately from test evidence duration. Enrollment curves subsample equal numbers of 4-s windows per enrolled identity from the enrollment block and repeat 10 times per duration. Test-evidence duration averages logistic posterior probabilities over consecutive windows within each test EDF.
- Artifact sensitivity uses band and channel subsets. This is a sensitivity analysis only; it cannot prove that residual identity information is neural rather than artifact-derived.

## Excluded operational claims

- Open-set DIR/FPIR is not reported as an operational result because a defensible independent unknown-identity calibration and final test require more identities than this 20-person cohort can provide at useful uncertainty. The old threshold procedure is retained only in the original results and is not carried into the corrected paper.
- The old posterior-based EER is not presented as calibrated verification. A future validation needs independent calibration participants and a prespecified claimed-identity trial protocol.

## Reproduction

From the project root run `python -m src.corrected_experiments` and then `python scripts/12_reviewer_response_analysis.py`. These write corrected outputs under `results/corrected/`; original outputs under `results/` are not overwritten. Version-matched features are cached with fit-scope metadata. MNE and Numba caches/config are redirected to `results/corrected/mne_home` and `results/corrected/numba_cache` for the managed Windows workspace. The reviewer-response script adds cohort/sex stratification, macro-F1, paired model tests, a matched diagnostic of historical full-session ICA features, subject-clustered test-duration CIs, and direction-specific normalized confusion matrices. Nearest-centroid and Mahalanobis implementations remain in the code but were not included in the completed comparison grid.
