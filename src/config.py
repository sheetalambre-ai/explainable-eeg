"""Central settings. Edit here, nowhere else."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"          # unzipped "EEG RAW Dataset.zip"
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"

SEED = 42
SFREQ = 256.0
# 16 channels are common to all files; A1/A2 are ear references -> dropped.
CHANNELS = ["FP1", "FP2", "F7", "F3", "F4", "F8", "T3", "T4",
            "T5", "T6", "P3", "P4", "O1", "O2"]
BANDS = {"delta": (1, 4), "theta": (4, 8), "alpha": (8, 13),
         "beta": (13, 30), "gamma": (30, 45)}
WINDOW_S = 4.0                           # non-overlapping analysis windows
PIPELINES = ["raw", "filtered", "ica"]   # Part A
LINE_FREQ = 50.0                         # India mains

# From EEG_Dataset_Description.pdf, Table 2 (subjects 1-10 Yemeni, 11-20 Indian).
NATIVE = {s: ("Arabic" if s <= 10 else "Hindi") for s in range(1, 21)}
SEX = {s: ("M" if s <= 12 else "F") for s in range(1, 21)}
