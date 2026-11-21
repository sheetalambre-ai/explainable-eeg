# Legacy outputs: read before using any number in this folder

The files at the top level of `results/` and in `results/figures/` come from the earlier exploratory pipeline
(scripts 01–10). They are kept for traceability. They are **not** corrected estimates, and no claim should be based
on them. The corrected estimates are in `results/corrected/`.

All results in this repository share three dataset-level limits (see the top-level `README.md`):
- one recording session per participant (identity ≡ session);
- Arabic block always first (script ≡ time);
- a task description that conflicts between sources (silent focus vs. speaking aloud).

| Files | Problem |
|---|---|
| `identity.csv`, `bio_*.csv`, `eegnet*.csv`, `log_identity.txt`, `log_bio.txt`, `log_eegnet*.txt` | ICA was fit on both blocks together (full-session ICA), so the test block was seen during preprocessing. |
| `bio_verification.csv` (EER), `bio_openset.csv` | Not operational results. With 20 identities there are no independent enrolment, calibration and test cohorts. |
| `bio_ablation.csv` (band, region and "emg_control" rows) | Full-session ICA. Restricting bands or sites does not exclude muscle or speech artifacts. Jaw, tongue and lip potentials are low-frequency. |
| `language_*.csv`, `log_language_*.txt`, `figures/fig2_language_splits.png` | The `window` and `file` schemes leak time within a recording. Under the `subject` scheme, Arabic-vs-Hindi decoding equals the early-vs-late time control, so the block label is not separable from time. |
| `did.csv`, `log_did.txt`, `figures/fig3_familiarity_did.png` | Familiarity and learning effects are unidentifiable without counterbalanced order. The result was null in any case. |
| `figures/fig1_quality.png`, `figures/fig4_biometrics.png`, `figures/fig5_confusion.png`, `tables.md` | Built from the legacy outputs above. Copies of three figures are in `paper/legacy/`. |
| `log_language*_FAILED_memory*.txt` | Logs of failed runs (out of memory), kept as a record. |
| `features_*.csv`, `quality.csv`, `file_index.csv` | Intermediate inputs. They contain no claims. |
