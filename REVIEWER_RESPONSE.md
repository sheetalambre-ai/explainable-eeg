# Response to the Six Review Concerns

> **Superseded (2026-11-21).** This document was written under the withdrawn "cross-script EEG identity recognition during reading" framing. The task may have been overt speech, identity is confounded with a single recording session, and script is confounded with time. See the status notice in `README.md`.

This response records the changes made to the analysis and six-section manuscript. Results are in `results/corrected/`; the paper is `paper/main.tex`.

## 1. Dataset and demographic confounding

Added cohort-stratified participant recall and macro-F1 for native-language/nationality groups and sex. Participants 1–10 are the Yemeni/Arabic-native cohort; 11–20 are the Indian/Hindi-native cohort. These labels are perfectly coupled in this sample. Sex is also imbalanced: all Arabic-native participants are male-coded; the Hindi-native group has two male-coded and eight female-coded participants.

For enrollment-only ICA power/logistic, Arabic-native versus Hindi-native mean recall is 97.1% versus 88.5% in Arabic→Hindi, and 96.1% versus 91.3% in Hindi→Arabic. The independent-group bootstrap CIs are wide, especially for the Hindi-native cohort. These data therefore show cohort heterogeneity but cannot say whether it reflects nationality, native language, sex, acquisition, or physiology. The manuscript makes no universal multilingual-invariance claim. A diverse independent cohort is still needed.

Artifacts: `group_aware_performance.csv`, `native_cohort_comparison.csv`, `demographic_cohort_map.csv`.

## 2. Preprocessing leakage

The corrected primary comparison uses fixed filtering/reference without ICA. Its sensitivity analysis fits ICA and selects components using enrollment data only, freezes that transform, and applies it to the opposite-language block. Scaling and hyperparameter tuning are also enrollment-only. Coherence is computed independently within each 4-s window without fitting across test windows.

For a matched diagnostic, the historical full-session ICA features were re-evaluated with the same file-level classifier tuning. They yield 93.1% and 94.6% balanced accuracy, compared with 92.8% and 93.7% for enrollment-only ICA. Paired participant differences are −0.3 and −0.9 percentage points, with Holm-adjusted p=0.685 and 0.578. Similar scores do not make test-distribution exposure acceptable; corrected enrollment-only fitting remains the paper's primary sensitivity result. The old and corrected feature generation differ in fit scope; the comparison should be interpreted as a diagnostic, not proof that leakage has no effect.

Artifacts: `leakage_audit.csv`, `legacy_full_session_ica_comparison.csv`, `legacy_full_session_ica_per_subject.csv`, `paired_participant_comparisons.csv`.

## 3. Same-session validation

The paper now consistently describes the task as **same-session cross-script identity recognition**. It explicitly states that the available data do not demonstrate cross-session generalization or long-term biometric permanence. Arabic files precede Hindi files for every participant; therefore language, fatigue, adaptation, and time/order cannot be separated. Counterbalanced blocks and repeated sessions require new data.

## 4. Statistical evidence and subject stability

The manuscript reports participant-bootstrap 95% CIs for balanced accuracy and macro-F1, per-person precision/recall/F1, direction-specific normalized confusion matrices, and paired participant-level model contrasts with Wilcoxon tests and Holm correction. None of the 12 tested representation/model/preprocessing contrasts survives Holm correction (smallest adjusted p=0.0766). Test-duration CIs first aggregate predictions within participant, avoiding treating windows or segments as independent replicates.

Primary macro-F1 is 92.2% (88.5–95.1) and 93.5% (90.7–95.7). Individual recall ranges from 50.0% to 100% and from 59.2% to 100%; two and one participants fall below 80% in the two directions. The high average is not uniform across identities.

Artifacts: `participant_macro_metrics.csv`, `per_subject_metrics.csv`, `paired_participant_comparisons.csv`, `test_evidence_duration_clustered.csv`, `test_evidence_duration_per_subject.csv`, normalized confusion CSVs, and `confusion_primary_directions.png`.

## 5. Muscle and other artifacts

The revised manuscript calls the low-frequency/site restriction a **sensitivity analysis** only. It says performance remains above chance but decreases; it does not claim EMG is ruled out or that the remaining signal is exclusively neural. The 40 enrollment-only ICA fits excluded no components. Direct EOG/EMG measurements and stronger artifact controls remain necessary.

## 6. Other methodological concerns

- **Open-set evaluation:** the earlier script divided 20 people into five four-person unknown groups, trained on the remaining 16 source-block identities, and evaluated all 20 identities in the target block. In each fold, the FPIR threshold was the score quantile of the four unknown identities in that same target test set; those very identities were also used to compute DIR. Thus the identity holdout did not provide independent threshold calibration. The old DIR figures are excluded as operational evidence. A separate calibration-identity set and final unknown-identity set would be needed, but 20 people cannot support those partitions with useful tail uncertainty.
- **Coherence:** computed independently per window; no test-informed cross-window connectivity fit is performed.
- **Window dependence:** uncertainty uses participant resampling after within-participant aggregation; segments/windows are not treated as independent people.
- **Paired tests:** paired participant recall contrasts use bootstrap intervals and Wilcoxon signed-rank tests, with Holm correction.
- **Novelty:** claims are limited to visual Arabic/Devanagari reading transfer. The manuscript cites the closest native/non-native auditory-language biometrics and prior cross-task EEG recognition.
- **Reproducibility:** scripts, corrected CSVs, per-subject outputs, separate direction confusion matrices, and the dataset manifest are present in the project. The LaTeX source still needs an actual compiler/PDF visual check before submission.
