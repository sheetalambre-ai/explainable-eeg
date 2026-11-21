# Dataset provenance audit

Generated from the on-disk files on 2026-11-21. No EDF was modified.

Participant folder names from the distributed archive are replaced by pseudonymous IDs (S1–S20). Absolute acquisition timestamps are replaced by per-participant offsets and a recording-day index.

## Identified source package

- Outer package: `EEG Dataset for Second Language Acquisition Arbic.zip` (1,120,111,654 bytes).
- Raw archive within the package: `EEG Dataset for Second Language Acquisition Arbic/EEG Dataset for Second Language Acquisition Arbic/EEG RAW Dataset.zip` (127,720,257 bytes).
- The outer package also contains a second ZIP with processed CSVs and a nested archive; it was not used to construct this EDF manifest.
- The manifest records pseudonymised relative paths, project-index header metadata, file sizes and CRC32 checks against the included raw ZIP.

## Raw archive reconciliation

- Included raw ZIP EDF entries: 296.
- Extracted local EDF files: 296.
- Extracted files matching the raw ZIP CRC32 and size: 296 / 296.
- ZIP EDF members with no same-named local file: 0.
- Local EDFs with no same-named ZIP member: 0.
- The current extraction agrees with the included `EEG RAW Dataset.zip`; it is not a 300-file extraction with four files omitted relative to that archive.

## Subject file counts and observed order

| Participant | EDF count | Arabic EDFs | Hindi EDFs | Header-time language order |
|---|---:|---:|---:|---|
| S1 | 10 | 5 | 5 | Arabic → Hindi |
| S2 | 15 | 7 | 8 | Arabic → Hindi |
| S3 | 15 | 7 | 8 | Arabic → Hindi |
| S4 | 15 | 7 | 8 | Arabic → Hindi |
| S5 | 15 | 7 | 8 | Arabic → Hindi |
| S6 | 15 | 7 | 8 | Arabic → Hindi |
| S7 | 15 | 7 | 8 | Arabic → Hindi |
| S8 | 15 | 7 | 8 | Arabic → Hindi |
| S9 | 14 | 7 | 7 | Arabic → Hindi |
| S10 | 15 | 7 | 8 | Arabic → Hindi |
| S11 | 15 | 7 | 8 | Arabic → Hindi |
| S12 | 15 | 7 | 8 | Arabic → Hindi |
| S13 | 14 | 7 | 7 | Arabic → Hindi |
| S14 | 15 | 7 | 8 | Arabic → Hindi |
| S15 | 15 | 7 | 8 | Arabic → Hindi |
| S16 | 15 | 7 | 8 | Arabic → Hindi |
| S17 | 15 | 7 | 8 | Arabic → Hindi |
| S18 | 18 | 7 | 11 | Arabic → Hindi |
| S19 | 15 | 7 | 8 | Arabic → Hindi |
| S20 | 15 | 8 | 7 | Arabic → Hindi |

## Chronology

- EDF measurement timestamps order Arabic files before Hindi files for every subject.
- Successive file start timestamps are 56 seconds apart; the project index reports 14,336 samples per EDF at 256 Hz.
- This establishes the local EDF chronology, not the exact displayed word within every file. The analysis files contain no event markers.

## Public metadata discrepancy and limits

- The current public Mendeley landing-page description states 300 raw EDFs and describes 15 per-participant recordings with Arabic/Hindi stimuli alternating. The included raw ZIP has 296 EDFs organized in participant/language directories; local header chronology is Arabic then Hindi.
- No four files are missing relative to the included raw archive. The archive does not explain why public landing-page metadata reports 300 or whether another release contains additional files.
- Do not claim exact word order or event timing from EDF headers. A recording log, event-marked data, or author clarification is needed.
- The EDF acquisition dates (2022) differ from package timestamps (2026); package time is not acquisition time.
- Recordings span 11 distinct recording days (`recording_day_index` in the manifest); several participants share a day.

## Task description conflict

- The dataset description asks participants to focus on each displayed word. Two of the dataset authors' papers (Aldhaheri et al. 2025, 2026) state that each word was spoken aloud. The task is therefore uncertain, and speech-related muscle or movement artifacts may be present.

## Demographic metadata

- Native language, nationality and sex coding comes from `src/config.py` and the dataset description, not EDF headers.
- Sex and native-language groups are unevenly distributed; this cohort cannot isolate language-background effects from sex/nationality.
- Ethics and consent claims should be attributed to the dataset record/source publication, not inferred from the raw archive.

## Regeneration

Run `python scripts/11_dataset_audit.py` from the project root. The script reads the existing file index and checks local CRC32/size against the raw ZIP directory. It writes `dataset_manifest.csv` and this report.
