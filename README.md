# Arabic/Hindi EEG blocks: same-session cross-block recording discrimination (archived exploratory analysis)

Leakage-conscious re-analysis of the Aldhaheri et al. Arabic/Hindi second-language EEG dataset
([Mendeley Data 7cdyp2r5cz](https://data.mendeley.com/datasets/7cdyp2r5cz)).

> [!WARNING]
> **Status (2026-11-21): archived. The original "cross-script EEG identity recognition during reading" framing
> is withdrawn, because the dataset cannot support it.**
>
> - **The task is documented inconsistently.** The dataset description asks participants to *focus on* each word.
>   Two of the dataset authors' papers (Aldhaheri et al. 2025, 2026) say each word was *spoken aloud*. The task
>   therefore cannot be called "reading", and speech-related muscle or movement artifacts may contribute to every
>   result here.
> - **Identity ≡ session.** Each participant has a single continuous recording on one date. Recognising the person
>   cannot be separated from recognising the session (cap fit, impedance, day, room).
> - **Script ≡ time.** Every participant did the Arabic block first, so script is confounded with time-on-task.
> - **The ICA step was inert.** Enrollment-only ICA removed 0 components in all 40 fits
>   (`results/corrected/leakage_audit.csv`), so no artifact removal took place.
> - Nationality, native language and sex are partly confounded, and recording dates cluster by group.
>
> What the results show is narrow: within one recording session, the 20 recordings remain discriminable across two
> consecutive stimulus blocks. They are **not** evidence of EEG biometrics, reading, language or L1/L2 effects,
> cross-session stability, or a neural origin of the signal.

The manuscript draft in [`paper/main.tex`](paper/main.tex) used the withdrawn framing and is not being submitted
(see [`paper/STATUS.md`](paper/STATUS.md)).

## Results (same-session, descriptive)

Closed-set 20-way balanced accuracy (chance 5%), 4-s windows, 95% participant-bootstrap CIs. The model is trained on
one block and tested on the other block of the same recording.
Full tables: [`results/corrected/RESULTS_SUMMARY.md`](results/corrected/RESULTS_SUMMARY.md).

| Preprocessing / features / model | Arabic block → Hindi block | Hindi block → Arabic block |
|---|---:|---:|
| Filtered, no ICA / band power / logistic | 92.4% (86.5–96.7) | 93.5% (88.9–96.7) |
| Enrollment-only ICA / band power / logistic | 92.8% (87.2–96.8) | 93.7% (89.2–96.8) |
| Enrollment-only ICA / power + coherence / logistic | 95.8% (92.9–98.0) | 96.2% (91.6–98.9) |

- No difference between models or feature types survives Holm correction (smallest adjusted p = 0.0766).
- Restricting features to 1–13 Hz, or to six sites, lowers accuracy to 74.9–90.7% but does **not** rule out muscle or
  speech artifacts. Jaw, tongue and lip movement potentials lie inside 1–13 Hz.
- Arabic-vs-Hindi decoding on unseen participants is no better than a pure early-vs-late time control
  (55.3–55.5% vs 55.0–55.1%; `results/language_filtered.csv`, `results/language_ica.csv`).

## Offline dashboard (not deployed)

[`dashboard/index.html`](dashboard/index.html) is a single self-contained file that runs offline. The earlier Vercel
deployment is no longer online.

- Its demo matches 32 s of EEG features to one of the 20 enrolled recordings. This is a closed set with no reject
  option, so any input is assigned to someone.
- The dashboard carries the same caveats as this README.
- Regenerate it with `python scripts/13_export_dashboard.py`.

## Setup

Python 3.10.

```bash
pip install -r requirements.txt
```

The dataset is **not** included in this repository. Download it from Mendeley Data and extract the raw EDF archive so
that files land at `data/raw/S<n>-<folder>/{Arabic,Hindi}/*.edf`. The folder names are as distributed by the dataset.

```bash
unzip "EEG Dataset for Second Language Acquisition Arbic/EEG Dataset for Second Language Acquisition Arbic/EEG RAW Dataset.zip" -d data/raw
python scripts/11_dataset_audit.py   # verifies 296/296 EDFs against the raw ZIP
```

`dataset_manifest.csv` and `DATASET_PROVENANCE.md` use pseudonymous IDs (`S1`–`S20`) and per-participant time offsets.
They contain no participant names and no acquisition dates.

## Reproducing the analyses

Corrected pipeline (enrollment-only ICA, nested file-level model selection, participant bootstraps, permutation
tests). Outputs go to `results/corrected/`.

```bash
python -m src.corrected_experiments
python scripts/12_reviewer_response_analysis.py
```

The earlier exploratory pipeline is **legacy**. Its outputs in `results/*.csv` and `results/figures/` used full-session
ICA, and some use leaky window- or file-level splits. See [`results/LEGACY.md`](results/LEGACY.md) before reading any
number from them.

```bash
python scripts/01_build_features.py      # raw / filtered / ICA pipelines -> window features, quality
python scripts/02_identity.py            # 20-way cross-block discrimination (legacy, full-session ICA)
python scripts/03_language.py            # block / time-control decoding (window/file schemes leak time)
python scripts/04_familiarity_did.py     # difference-in-differences (unidentifiable here; null result)
python scripts/05_figures.py             # legacy figures + results/tables.md
python scripts/06_biometrics.py          # duration, EER, band/region ablations (legacy)
python scripts/07_cache_windows.py       # cache ICA-cleaned windows (results/windows_ica.npz)
python scripts/08_eegnet.py              # EEGNet baseline (legacy, full-session ICA)
python scripts/08b_eegnet_tuned.py       # EEGNet tuned on training-block validation only (legacy)
python scripts/09_coherence.py           # coherence baseline (legacy)
python scripts/10_subjects_openset.py    # per-subject, bootstrap CIs, open-set (legacy; not an operational result)
```

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for exact settings and
[`METHODOLOGY_CHANGES.md`](METHODOLOGY_CHANGES.md) for why the corrected pipeline differs.

## Repository layout

| Path | Contents |
|---|---|
| `src/` | `config.py` settings · `data.py` file index/loading · `features.py` preprocessing + band power · `evaluate.py` models/CV/permutation · `eegnet.py` · `corrected_experiments.py` |
| `scripts/` | Numbered analysis scripts (above) |
| `results/corrected/` | Primary (corrected) estimates |
| `results/` (top level) | Legacy outputs, see `results/LEGACY.md` |
| `paper/` | Withdrawn manuscript draft and figures; `paper/legacy/` holds figures built from legacy outputs |
| `references/REFERENCES_CATALOG.md` | Cited literature (PDFs not redistributed) |
| `*.md` (root) | Audit, protocol, provenance, literature review, changelog (written before the 2026-11-21 status change) |

## Dataset facts

- 296 EDF files, 20 participants. 14 common scalp channels are analysed. The EDFs hold 16–18 channels, although the
  sources describe a 40-electrode system.
- Each participant has one continuous recording on one date, split into consecutive 56-s files.
- Every participant did the whole Arabic block first, then Hindi.
- There are no event markers, so analysis uses 4-s windows at block level.
- The sources disagree on:
  - the task: focus on each word vs. speak it aloud;
  - the word duration: 5 s vs. 10 s;
  - the participant count: 8, 10 or 20 in different papers;
  - the file count: 300 documented vs. 296 released.

## Citation

If you use this code, please also cite the original dataset (Aldhaheri et al., Mendeley Data 7cdyp2r5cz).
