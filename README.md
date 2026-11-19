# Cross-Script EEG Identity Recognition (Arabic ↔ Hindi)

Leakage-conscious re-analysis of the Aldhaheri et al. Arabic/Hindi second-language EEG dataset
([Mendeley Data 7cdyp2r5cz](https://data.mendeley.com/datasets/7cdyp2r5cz)). The main question:
can a person be identified from EEG recorded while reading one script (Arabic) using a model
enrolled on the other (Hindi), and vice versa?

Manuscript: [`paper/main.tex`](paper/main.tex) — *Cross-Script EEG Identity Recognition During Arabic
and Hindi Reading: A Leakage-Conscious Transfer Study* (IEEEtran).

## Headline results

Closed-set 20-way balanced accuracy (chance 5%), 4-s windows, 95% participant-bootstrap CIs.
Full tables: [`results/corrected/RESULTS_SUMMARY.md`](results/corrected/RESULTS_SUMMARY.md).

| Preprocessing / features / model | Arabic → Hindi | Hindi → Arabic |
|---|---:|---:|
| Filtered, no ICA / band power / logistic | 92.4% (86.5–96.7) | 93.5% (88.9–96.7) |
| Enrollment-only ICA / band power / logistic | 92.8% (87.2–96.8) | 93.7% (89.2–96.8) |
| Enrollment-only ICA / power + coherence / logistic | 95.8% (92.9–98.0) | 96.2% (91.6–98.9) |

Aggregating 32 s of test evidence raises power/logistic accuracy to ~97.5–97.9%.
Caveats (same-session recordings, fixed block order, group/sex/date confounds, possible artifact
contributions) are documented in [`IEEE_READINESS.md`](IEEE_READINESS.md) and
[`REVIEWER_RESPONSE.md`](REVIEWER_RESPONSE.md).

## Presentation dashboard

Live: https://dashboard-ten-virid-83.vercel.app — or open [`dashboard/index.html`](dashboard/index.html) in any browser — it is a single self-contained file that runs fully offline (no server, no internet). It has a live demo that identifies a participant from 32 s of EEG features (built-in samples or your own CSV, e.g. [`dashboard/samples/`](dashboard/samples/)), the main results charts, and a plain-language explainer. Regenerate it with `python scripts/13_export_dashboard.py`.

## Setup

Python 3.10.

```bash
pip install -r requirements.txt
```

The dataset is **not** included in this repository. Download it from Mendeley Data and extract the
raw EDF archive so that files land at `data/raw/S<n>-<name>/{Arabic,Hindi}/*.edf`:

```bash
unzip "EEG Dataset for Second Language Acquisition Arbic/EEG Dataset for Second Language Acquisition Arbic/EEG RAW Dataset.zip" -d data/raw
python scripts/11_dataset_audit.py   # verifies 296/296 EDFs against dataset_manifest.csv
```

## Reproducing the analyses

Corrected (primary) pipeline — enrollment-only ICA, nested file-level model selection,
participant bootstraps and permutation tests; outputs go to `results/corrected/`:

```bash
python -m src.corrected_experiments
python scripts/12_reviewer_response_analysis.py
```

Earlier exploratory pipeline (historical; outputs in `results/`):

```bash
python scripts/01_build_features.py      # raw / filtered / ICA pipelines -> window features, quality
python scripts/02_identity.py            # 20-way subject identification, cross-language
python scripts/03_language.py            # stimulus / time-control / L1-vs-L2 decoding
python scripts/04_familiarity_did.py     # difference-in-differences familiarity test
python scripts/05_figures.py             # figures + results/tables.md
python scripts/06_biometrics.py          # duration, EER, band/region/EMG ablations
python scripts/07_cache_windows.py       # cache ICA-cleaned windows (results/windows_ica.npz)
python scripts/08_eegnet.py              # EEGNet baseline (GPU), 3 seeds
python scripts/08b_eegnet_tuned.py       # EEGNet tuned on training-language validation only
python scripts/09_coherence.py           # coherence connectivity baseline
python scripts/10_subjects_openset.py    # per-subject, bootstrap CIs, open-set
```

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for exact settings and
[`METHODOLOGY_CHANGES.md`](METHODOLOGY_CHANGES.md) for why the corrected pipeline differs.

## Repository layout

| Path | Contents |
|---|---|
| `src/` | `config.py` settings · `data.py` file index/loading · `features.py` preprocessing + band power · `evaluate.py` models/CV/permutation · `eegnet.py` · `corrected_experiments.py` |
| `scripts/` | Numbered analysis scripts (above) |
| `results/` | All CSVs behind the paper; `results/corrected/` holds the primary estimates |
| `paper/` | LaTeX manuscript and figures |
| `references/REFERENCES_CATALOG.md` | Cited literature (PDFs not redistributed) |
| `*.md` (root) | Audit, protocol, provenance, literature review, changelog |

## Dataset facts (verified from EDF headers)

- 296 EDF files, 20 participants; 14 scalp channels after dropping A1/A2 ear references.
- Each "See" file is a consecutive 56-s chunk of one continuous recording.
- Every participant saw the whole Arabic block first, then Hindi — stimulus language is
  confounded with time-on-task.
- No event markers, so analysis uses 4-s windows at block level.
- Group (Yemeni/Indian) is confounded with sex and recording date.

## Citation

If you use this code, please also cite the original dataset (Aldhaheri et al., Mendeley Data 7cdyp2r5cz).
