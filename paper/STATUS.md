# Manuscript status: withdrawn (2026-11-21)

`main.tex` ("Cross-Script EEG Identity Recognition During Arabic and Hindi Reading: A Leakage-Conscious Transfer
Study") is a draft that will **not** be submitted. Its framing is not supported by the dataset:

- **"Reading."** The dataset description asks participants to focus on each word. Two of the dataset authors' papers
  (Aldhaheri et al. 2025, 2026) say each word was spoken aloud. The draft does not mention this.
- **"Identity recognition."** Each participant has one recording session, so identity cannot be separated from the
  session.
- **"Cross-script."** Arabic always came first, so script is confounded with time-on-task.

The numbers in the draft come from `results/corrected/` and are correct as computed. Their interpretation is limited
to same-session cross-block discrimination of 20 recordings.

`legacy/` holds three figures built from the legacy pipeline (see `results/LEGACY.md`). The draft does not use them.
