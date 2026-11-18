"""File index + per-subject loading (files are consecutive chunks of one recording)."""
import re
import mne
import pandas as pd
from .config import RAW_DIR, CHANNELS, NATIVE, SEX

mne.set_log_level("ERROR")
NAME_RE = re.compile(r"S(\d+)-([AH])-See(\d+)\.edf$", re.I)


def index_files() -> pd.DataFrame:
    """One row per EDF with subject/language/time metadata, in recording order."""
    rows = []
    for f in sorted(RAW_DIR.glob("*/*/*.edf")):
        m = NAME_RE.search(f.name)
        subj, lang, chunk = int(m[1]), {"A": "Arabic", "H": "Hindi"}[m[2].upper()], int(m[3])
        info = mne.io.read_raw_edf(f, preload=False)
        rows.append(dict(path=str(f), subject=subj, language=lang, chunk=chunk,
                         start=info.info["meas_date"], n_samples=info.n_times, native=NATIVE[subj], sex=SEX[subj]))
    df = pd.DataFrame(rows).sort_values(["subject", "start"]).reset_index(drop=True)
    df["order"] = df.groupby("subject").cumcount()              # position in session
    t0 = df.groupby("subject")["start"].transform("min")
    df["minutes"] = (df["start"] - t0).dt.total_seconds() / 60
    df["familiarity"] = (df["language"] == df["native"]).map({True: "L1", False: "L2"})
    df["file_id"] = df["subject"].astype(str) + "_" + df["order"].astype(str)
    return df


def load_subject(files: pd.DataFrame) -> mne.io.Raw:
    """Concatenate one subject's files in time order, keeping the common channels."""
    raws = [mne.io.read_raw_edf(p, preload=True).pick(CHANNELS) for p in files["path"]]
    for r in raws:
        r.reorder_channels(CHANNELS)
    raw = mne.concatenate_raws(raws)
    raw.set_montage("standard_1020", match_case=False, on_missing="ignore")
    return raw
