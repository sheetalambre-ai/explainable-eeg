# IEEE Conference Readiness and Reviewer Assessment

Assessment date: 2026-11-13. This is a critical internal review, not a prediction of any committee's decision.

## Recommendation

The work is suitable for submission as an **exploratory neural-signal transfer study** after a reproducibility and manuscript check, but it is not yet persuasive as a general EEG biometric system. The corrected estimate is credible for the narrow within-session, cross-block question because data-adaptive preprocessing and model selection were confined to enrollment; fixed filtering/reference and the frozen enrollment ICA were applied to the test data. A cautious neural-engineering conference is a better fit than a biometric-security venue. IEEE EMBS Neural Engineering 2027 is the preferred target by scope and page allowance (4–7 pages including references); IEEE EMBC 2027 is a possible but compressed alternative (four technical pages plus a references-only page, max 20 references). Verify deadlines and requirements on the official [NER 2027 submission page](https://neuro.embs.org/2027/papers/) and [EMBC 2027 CFP](https://embc.embs.org/2027/papers/) before submission.

The six-section paper at `paper/main.tex` is intentionally focused. The author/affiliation fields still need completion. It has not been compiled: no local LaTeX compiler was found, so page count, figure layout, bibliography formatting, and IEEE compliance remain unverified.

## What is and is not novel

**Defensible novelty:** an audited evaluation of transfer between visual Arabic- and Devanagari-script reading blocks, comparing spectral power, coherence, and fused features with participant-level uncertainty and enrollment-only preprocessing on a 14-channel recording. This is a narrow experimental condition and protocol contribution.

**Claims to avoid:** first language-conditioned EEG biometric; first task-independent EEG identity signature; language-invariant neural identity; artifact-free or neural-only identity; deployable authentication; new dataset.

The closest direct comparator is Sah, Ahirwal, and Tomar, IEEE SCEECS 2025, DOI `10.1109/SCEECS64059.2025.10940880`. It studies native/non-native-language songs and neutral music, with auditory stimulation and a 1-D CNN; its IEEE record reports sensitivity 0.9666, specificity 0.9982, and EER 0.0318. It directly defeats a broad “language has not been studied in EEG biometrics” framing, but does not test visual script reading or the same split, cohort, and metrics. Mota et al. (PeerJ Computer Science, 2021; DOI `10.7717/peerj-cs.549`) provide an established cross-task motor/motor-imagery comparison, precluding claims that cross-task EEG identity itself is novel. Del Pozo-Baños et al. (2018; DOI `10.1142/S0129065717500356`) report task-independent spectral identity signatures, similarly narrowing novelty.

Three Arabic/Hindi second-language studies (2024, 2025, 2026) concern language/learning classification rather than participant identity. They are a related same-data research line, not directly comparable biometric baselines. The 2024 and 2025 papers use smaller cohorts and the 2026 paper reports 20 participants; resolve dataset-release lineage before claiming independent replication. The Mendeley page currently lists 300 EDFs while the packaged raw archive and this analysis contain 296 matching EDFs. Do not speculate about the four-file discrepancy.

## Strengths

- The original full-session ICA test-distribution exposure in the cross-block evaluation was identified and corrected. This was not label leakage, but the old decomposition included the test block; the primary result fits data-adaptive transforms and model hyperparameters on enrollment only.
- All 296 extracted EDFs match the included raw ZIP by both byte size and CRC32; the manifest and archive mismatch are documented.
- Both transfer directions are reported, with participant-level confidence intervals, participant-preserving permutation tests, file-grouped enrollment-only tuning, and separate enrollment/test-duration analyses.
- Native-language/nationality and sex subgroup summaries, macro-F1, individual stability counts, normalized direction-specific confusion matrices, paired participant contrasts, and a matched legacy full-session ICA diagnostic are now included.
- The manuscript has six substantive numbered sections, reports the closest direct language-conditioned study, and removes unsupported open-set, EER-calibration, and neural-specificity claims.

## Main weaknesses and likely rejection grounds

1. **Order and language are inseparable (major).** Arabic always precedes Hindi. Identity recognition across blocks is shown, but differences between language, time, fatigue, adaptation, and drift cannot be identified causally. Counterbalanced order or a repeated/counterbalanced protocol is the most important new data requirement.
2. **Only one session and 20 identities (major).** The results do not demonstrate permanence or external generalization. A single-session test can exploit person-specific electrode placement, impedance, or acquisition traces shared across blocks.
3. **Closest prior work reduces novelty (major).** The paper must emphasize the visual script-transfer setting, not language-invariance in general. A reviewer may see this as a dataset reuse and a narrow task variation unless the experimental control and analysis contribution are clear.
4. **Missing corrected modern/classical baselines (moderate-major).** No corrected EEGNet/deep feature, random forest, nearest-centroid, or Mahalanobis result is reported. Previous EEGNet numbers use full-session ICA and must not be compared as if corrected. The final classifier grid is therefore useful but incomplete.
5. **No independent verification/open-set protocol (moderate).** Closed-set identification alone is an incomplete biometric evaluation. The decision not to claim EER/open-set performance is methodologically sound, but leaves no deployment-level evidence.
6. **Artifact ambiguity (major).** There are no explicit EOG/EMG controls or independent electrode-artifact checks; no ICA components were excluded in any of the 40 fits. Band/site restrictions show residual information but cannot establish its neural source.
7. **Uncertainty and representation ranking (moderate).** Paired participant bootstrap/Wilcoxon comparisons are complete; none of 12 contrasts survives Holm correction (smallest adjusted p=0.077). Coherence/fusion should not be presented as reliably superior to power.
8. **Enrollment-duration estimate is descriptive (moderate).** It uses the C selected on the complete enrollment block and only ten subsamples. A deployment claim would require a nested duration-specific selection procedure, repeated seeds, and a specified enrollment protocol.
9. **Archive and manuscript finalization (minor but preventable).** The 296-versus-300 provenance mismatch remains unresolved. LaTeX has not been compiled and NER's page limit has not been checked on an actual PDF.

## Prioritized experiments before a strong resubmission

1. Obtain or collect recordings with counterbalanced language/script order and repeat sessions; use subject-disjoint external testing where possible.
2. Add explicit EOG/EMG channels or principled artifact controls; report whether any ICA components are selected and verify with blinded review.
3. Re-run EEGNet and at least one additional established baseline (e.g., random forest or task-independent spectral descriptor) using exactly the corrected split and preprocessing. Include class-balanced chance and simple nearest-centroid baselines.
4. Done for the present cohort: paired participant contrasts, macro-F1, per-subject outputs, group summaries, and normalized confusion matrices have been added. A future study should predeclare the primary representation/model and validate it in an independent cohort.
5. For biometric claims, design disjoint enrollment/calibration/test identities and report verification ROC/DET, EER with participant-level uncertainty, and open-set DIR/FPIR at fixed operating points. If the cohort cannot support this, continue to frame the work as identification research.
6. Resolve dataset provenance with a release manifest or author clarification; then compile the six-section source and fit the exact target venue's page/reference rules.

## Likely reviewer summary

**Positive:** a relevant, multilingual neural-data question; clear test-block leakage correction; careful provenance and participant-level reporting; strong above-chance within-session transfer.

**Negative:** fixed block order and one session undermine the invariance interpretation; the cohort is small; direct auditory-language biometrics already exist; the artifact source and independent biometric utility remain untested; corrected baseline suite is incomplete.

**Overall:** promising exploratory conference paper after PDF verification, with substantial rejection risk if framed as a robust language-invariant biometric rather than a limited cross-script transfer experiment.
