# Changelog

## 2026-11-21

- Withdrew the "cross-script EEG identity recognition during reading" framing. Reasons: the dataset sources conflict on the task (focus vs. speaking aloud), identity is confounded with a single recording session, and script is confounded with time. The manuscript draft will not be submitted (`paper/STATUS.md`).
- Rewrote `README.md` with a status notice and narrowed the result descriptions. Removed the link to the Vercel deployment, which is no longer online.
- Corrected unsupported dashboard claims in `dashboard/template.html` (reading, fingerprint, brain connectivity, muscle-artifact panel, ICA cleaning, demo confidence wording) and regenerated `dashboard/index.html`.
- Pseudonymised `dataset_manifest.csv` and `DATASET_PROVENANCE.md`: participant folder names replaced by S1–S20, and absolute acquisition timestamps replaced by per-participant offsets and a recording-day index. Updated `scripts/11_dataset_audit.py` to write these outputs.
- Added `results/LEGACY.md` and moved three unused legacy figures to `paper/legacy/`. Added superseded banners to the earlier assessment documents.

## 2026-11-13

- Added `RESEARCH_AUDIT.md` before manuscript changes.
- Added `scripts/11_dataset_audit.py`, `dataset_manifest.csv`, and `DATASET_PROVENANCE.md`; confirmed 296/296 extracted EDFs match the included raw archive by CRC32 and size.
- Added `src/corrected_experiments.py` with enrollment-only ICA, no-ICA sensitivity, file-level nested model comparison, participant-level uncertainty, duration analyses, feature caches, and checkpointed output tables.
- Added `LITERATURE_REVIEW.md`; incorporated the close 2025 IEEE native/non-native-language auditory biometric study into novelty positioning.
- Added `EXPERIMENT_PROTOCOL.md`, `REPRODUCIBILITY.md`, and `METHODOLOGY_CHANGES.md`.
- Existing results and paper have not been overwritten; corrected outcomes are being written under `results/corrected/`.
- Completed the corrected comparison grid, duration analyses, artifact sensitivity, participant bootstrap intervals, and subject-preserving permutation tests; outputs are under `results/corrected/`.
- Replaced `paper/main.tex` with the corrected six-section manuscript and preserved the previous draft as `paper/main_original_draft.tex`.
- Added `IEEE_READINESS.md` and `results/corrected/RESULTS_SUMMARY.md` with results, remaining weaknesses, and submission assessment.
- Added `scripts/12_reviewer_response_analysis.py` and `REVIEWER_RESPONSE.md`; generated native-language/nationality and sex-stratified summaries, macro-F1 CIs, paired participant tests, matched full-session ICA comparison, clustered test-duration CIs, and direction-specific normalized confusion matrices. Updated the six-section paper to report these analyses and narrow artifact/session/demographic claims.
- Re-ran the corrected experiment grid to restore a complete, consistent 20-row model summary after detecting a stale partial checkpoint; re-ran reviewer-response summaries from the regenerated subject-level outputs.
