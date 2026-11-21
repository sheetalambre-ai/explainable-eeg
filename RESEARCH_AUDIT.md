# Research Audit

> **Superseded (2026-11-21).** This document was written under the withdrawn "cross-script EEG identity recognition during reading" framing. The task may have been overt speech, identity is confounded with a single recording session, and script is confounded with time. See the status notice in `README.md`.

Audit date: 2026-11-13 (Asia/Calcutta)

## 1. Repository and reproducibility state

- The project contains raw EDF data, the outer Mendeley data archive, Python source and scripts, cached features/windows, result CSVs/logs, and an IEEEtran LaTeX draft.
- No Git repository metadata is present in this workspace. Original scripts, CSVs, logs, and manuscript are therefore being preserved; corrections will be placed in separate files and `results/corrected/`.
- Python 3.10.10 is available with MNE, NumPy, pandas, SciPy, scikit-learn, PyTorch, and Matplotlib. The original results logs show the identity and biometric runs completed. PyTorch device availability and LaTeX compiler availability remain to be checked.
- Existing figures are present under `results/figures/`; no PDF manuscript build has yet been verified.

## 2. Dataset and current analysis

- The extracted local raw directory contains 296 EDFs from 20 subjects, sampled at 256 Hz. The processed feature table contains 4,144 non-overlapping 4-s windows. Channels common to all files are the 14 listed in `src/config.py`; A1/A2 are excluded.
- The project index orders files using EDF measurement timestamps. In the currently analyzed archive, Arabic files precede Hindi files for each subject, and adjacent EDF timestamps are 56 s apart. Thus transfer direction is also tied to recording time.
- Each 4-s window is summarized with Welch PSD, five frequency bands, and log/relative powers (140 features). The main classifier is standardization plus L2 logistic regression; other existing analyses include random forest, coherence, EEGNet, language decoding, a difference-in-differences analysis, duration, verification, and open-set scoring.
- Preprocessing variants are raw; notch (50/100 Hz), 1–45 Hz filtering and average reference; and the latter plus FastICA ocular-component exclusion.
- Critical implementation finding: `scripts/01_build_features.py` and `scripts/07_cache_windows.py` preprocess each subject's concatenated Arabic and Hindi data together. FastICA is therefore fit with both enrollment and test blocks in the cross-block evaluation.

## 3. Existing headline results (reproduced from saved logs/CSVs)

- ICA + logistic regression: Arabic→Hindi balanced accuracy 0.9133; Hindi→Arabic 0.9401.
- Duration aggregation: 16-s accuracy 0.9636 / 0.9714; 32-s accuracy 0.9763 / 0.9750, respectively.
- 16-s posterior-score EER: 0.0154 / 0.0106. These are preliminary because the current trial construction and uncertainty treatment do not establish operational biometric calibration.
- Coherence logistic regression: 0.9492 / 0.9623; power + coherence: 0.9538 / 0.9689.
- EEGNet tuned with training-block validation: mean 0.712 / 0.789 across three seeds. Existing EEGNet windows inherit full-session ICA preprocessing.
- Within-language early→late identification: Arabic 0.9696; Hindi 0.9821. This is a useful time-control but does not separate time from the cross-language block change.
- Language decoding difference-in-differences finds no feature surviving FDR at q<0.05. This should not be presented as a powered demonstration of no familiarity effect.

## 4. Inconsistencies and weaknesses

1. **Preprocessing leakage:** ICA is fit on concatenated train and test blocks; corrected primary estimates must not use this cache.
2. **Order confounding:** Arabic is always first, Hindi second. No causal language-invariance claim is supported.
3. **Data provenance:** the local extracted tree and raw zip contain 296 EDFs. The current Mendeley landing-page description reports 300 EDFs and describes a session/stimulus schedule that needs reconciliation with the actual files. The existing outer archive contains both `EEG RAW Dataset.zip` and a separate processed-CSV ZIP; these may be different representations/releases and must not be silently mixed.
4. **Inference:** windows are correlated; subject is the primary replication unit. Existing confidence intervals are useful but not every comparison/permutation is subject-preserving.
5. **Open-set calibration:** the current test-fold unknown identities are used to choose a threshold for that same fold's DIR result.
6. **Verification:** the current posterior scores and pooled windows need a declared claimed-identity trial design, independent threshold calibration, and participant-level uncertainty.
7. **Artifacts:** low-frequency/channel ablations are sensitivity analyses, not proof of neural-only identity information.
8. **Cohort:** 20 subjects in one session, with sex and nationality unevenly distributed; no cross-session stability or demographic generalization is established.
9. **Model selection:** several useful baselines exist, but no matched set of regularized LDA/SVM/centroid/Mahalanobis models with training-block-only nested tuning.
10. **Enrollment cost:** test evidence duration is reported; training/enrollment duration is not systematically varied.
11. **Manuscript:** the draft contains author placeholders and makes claims that must be narrowed after corrected results. Citation completeness, conference page budget, and a compiled PDF require a final check.

## 5. Required corrections and experiments

- Generate a file-level manifest from the extracted tree and both nested archives; identify version/source differences and missing files without fabricating them.
- Rebuild analysis features from raw EDFs under a no-ICA filtered/average-reference primary pipeline. Add a separate ICA sensitivity pipeline that fits ICA and chooses exclusions on the enrollment block only, applies the fitted transform to the test block, and records excluded components and channel order.
- Re-run both transfer directions; report each separately and use participant-level bootstrap intervals and participant-preserving paired comparisons.
- Add regularized/shrinkage LDA, SVM, nearest centroid, and Mahalanobis baselines with group-aware tuning confined to enrollment files. Compare spectral, coherence, and fused representations under the same protocol.
- Evaluate enrollment duration separately from test evidence duration.
- Replace the current operational open-set claims unless enrollment/calibration/test identities can be partitioned independently. With only 20 subjects, report any exploratory split as non-independent/limited if necessary.
- Keep verification claims only if a defensible independent threshold calibration and participant-level evaluation can be constructed; otherwise move them to exploratory appendix or omit from the short conference paper.
- Retain feature/channel/frequency sensitivity analyses but use cautious artifact language.
- Rewrite the manuscript only after corrected outputs are available, with six or seven substantive numbered sections as requested by the author.

## 6. Prioritized implementation plan

1. **Audit/provenance:** create `dataset_manifest.csv`, `DATASET_PROVENANCE.md`, and this audit.
2. **Leakage-safe features:** add corrected scripts and write only to `results/corrected/`; preserve current result files.
3. **Primary model comparisons:** run both directions, matched features/models, subject-level estimates, and enrollment-duration analysis.
4. **Secondary analyses:** evaluate artifact sensitivities and determine whether open-set/verification claims can be supported by an independent calibration design.
5. **Literature and paper:** verify primary sources/DOIs, rewrite a concise 6–7-section paper, update figures/tables, compile if tooling is available, and document unresolved limitations.

## 7. Computational requirements and current feasibility

- Existing extracted EDF data and feature caches are available, and required scientific Python packages are installed.
- Python 3.10.10, MNE 1.12.1 and CUDA are available. No local `pdflatex`, `xelatex`, `latexmk`, or `tectonic` command was found; PDF compilation and pagination remain outstanding.
- Corrected feature extraction requires re-reading the EDFs and should be run once per needed pipeline/direction; full-session ICA caches must not be reused for corrected headline results.
- The original EEGNet tuning run is computationally costly and need not be repeated unless a corrected filtered-data comparison remains feasible after the primary analyses.
- Current dataset provenance cannot be resolved from the local extracted tree alone if the Mendeley release history or the separately packaged processed-CSV ZIP lacks a clear version map. The two archives will be inventoried separately.
- A final IEEE PDF is contingent on an installed LaTeX toolchain and the selected conference's current official page limit.

## 8. Completion addendum (2026-11-13)

- Completed the corrected comparison using cached, version-matched features. The finished table contains 20 model/representation/direction/preprocessing rows, per-subject metrics, 40 enrollment-only ICA audit rows, duration analyses, 10 feature ablations, and confusion matrices.
- The enrollment-only ICA logistic power result is 92.8% Arabic→Hindi and 93.7% Hindi→Arabic balanced accuracy, both participant-label permutation p=0.0005. Filtered no-ICA results are 92.4% and 93.5%; the original full-session ICA estimates are not used as corrected results.
- No ocular-correlated components were excluded in any of the 40 ICA fits; the data do not show that ICA cleaning improves scores.
- Corrected baselines are logistic regression, shrinkage LDA, and linear SVM for power, plus logistic regression for coherence and fusion. Nearest-centroid, Mahalanobis, corrected EEGNet, and random-forest baselines are not complete and remain gaps.
- The original draft is preserved as `paper/main_original_draft.tex`; `paper/main.tex` now has six sections and narrowed claims. See `IEEE_READINESS.md` and `results/corrected/RESULTS_SUMMARY.md` for the paper review and results.
- Remaining before submission: complete author metadata; compile and visually inspect the PDF; verify the target page limit on that PDF; disclose the 296/300 archive metadata discrepancy; prioritize counterbalanced order, repeated-session data, and direct artifact controls for stronger claims.
- Reviewer-response pass added native-language/nationality and sex subgroup summaries, macro-F1 with participant-bootstrap intervals, individual performance ranges, paired participant contrasts with Holm correction, a matched re-evaluation of full-session ICA features, participant-clustered test-duration intervals, and separate normalized confusion matrices. The manuscript still frames these as same-session cross-script results and does not claim cohort-independent or long-term invariance.
- Subgroup results show higher recall for the Arabic-native/Yemeni cohort in both directions, with broad intervals. Since native language and nationality are perfectly associated and sex is imbalanced, the differences cannot be attributed to a specific demographic or physiological cause.
- Paired model/preprocessing comparisons do not establish a reliable winner after Holm correction. The previously reported open-set threshold used unknown identities from the same test set for calibration; those operational claims are withdrawn. The revised method explains the five-fold/four-unknown design and why it is not independent calibration.
