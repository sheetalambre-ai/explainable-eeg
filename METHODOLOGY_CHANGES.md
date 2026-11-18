# Methodology Changes

## Implemented in corrected code

1. **Training-only ICA:** FastICA fit and ocular-component selection are performed on the enrollment-language block for each participant and direction. The fitted transform is applied unchanged to the held-out block. Channels and ordering are checked before application. The no-ICA filtered pipeline is also run as a sensitivity baseline.
2. **Archive provenance:** all 296 local EDFs are matched against the included raw ZIP by CRC32 and uncompressed byte count; the manifest includes the participant/file mapping and header-index fields. This resolves extraction parity for the included archive, but not why the public landing page lists 300 EDFs.
3. **File-aware model selection:** evaluated logistic regression, shrinkage LDA, and linear SVM for power features, plus logistic regression for coherence and fused features. Hyperparameters are selected by 3-fold file-level validation inside enrollment only; feature standardization is fit inside the model pipeline. No learned feature selection uses held-out data; frequency/site subsets are fixed sensitivity analyses. Nearest-centroid and shared-covariance Mahalanobis were not run to completion and are not claimed as baselines.
4. **Subject-level evaluation:** balanced accuracy and macro-F1 are accompanied by participant precision/recall/F1, participant bootstrap intervals, direction-specific normalized confusion matrices, and a label-mapping permutation test for the predeclared main comparison. Native-language/nationality and sex-stratified summaries, participant-level paired contrasts, and Holm-adjusted Wilcoxon tests were added.
5. **Enrollment and test duration separated:** enrollment sample-count curves and held-out test posterior-aggregation curves are separate outputs.
6. **Artifact sensitivity cautious:** low-frequency and restricted-channel ablations are re-evaluated after training-only ICA. They do not support a claim that the surviving signal is exclusively neural.

## Deliberately not claimed

- No causal language effect: Arabic is always earlier than Hindi in this local recording sequence.
- No cross-session permanence: all observations are from one session.
- No calibrated open-set DIR/FPIR or operational verification: 20 identities are insufficient for a stable independent calibration/test split, and the former procedure reused test unknowns for threshold selection.
- No neural-only identity interpretation: ocular/muscle/electrode and other acquisition effects remain possible.
- No claim that language-conditioned EEG biometrics are entirely unstudied: a 2025 IEEE study tested native- and non-native-language songs for EEG biometrics. The narrower contribution is visual cross-script transfer for Arabic/Hindi reading conditions.
- No deep-network baseline under corrected preprocessing: the existing EEGNet result uses earlier full-session ICA features and is excluded from corrected manuscript claims.

## Required for a stronger follow-up

Counterbalanced language order, event markers or verified stimulus logs, additional participants, separate recording sessions, EOG/EMG channels or stronger artifact controls, and separate enrollment/calibration/final-test identity cohorts.
