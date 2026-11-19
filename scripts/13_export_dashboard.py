"""Export compact models, sample input files and result tables for the offline dashboard.

Trains the paper's filtered/no-ICA band-power logistic model (C=1) on one language block and
writes everything the dashboard needs into dashboard/index.html (self-contained, no network).
"""
import json, re
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results/corrected/feature_cache"
RES = ROOT / "results/corrected"
OUT = ROOT / "dashboard"
# (participant, start window within block, label) - a mix of easy, uncertain and wrong cases
SAMPLES = {
    "Arabic->Hindi": [(8, None, "clear"), (18, 48, "windows disagree"), (13, 40, "uncertain"), (13, 56, "misidentified")],
    "Hindi->Arabic": [(19, None, "clear"), (2, 8, "windows disagree"), (2, 0, "misidentified"), (11, 8, "misidentified")],
}
SAMPLE_WINDOWS = 8  # 8 x 4 s = 32 s of EEG


def load(lang):
    parts = [np.load(f, allow_pickle=True) for f in sorted(CACHE.glob(f"filtered_s*_{lang}.npz"))]
    X = np.vstack([p["power"] for p in parts]).astype(float)
    y = np.concatenate([p["subject"] for p in parts])
    return X, y, [str(n) for n in parts[0]["feature_names"]]


data, samples = {}, []
for train, test in [("Arabic", "Hindi"), ("Hindi", "Arabic")]:
    Xtr, ytr, names = load(train)
    Xte, yte, _ = load(test)
    sc = StandardScaler().fit(Xtr)
    m = LogisticRegression(C=1.0, max_iter=3000, random_state=0).fit(sc.transform(Xtr), ytr)
    key = f"{train}->{test}"
    acc = float((m.predict(sc.transform(Xte)) == yte).mean())
    data.setdefault("models", {})[key] = {
        "train": train, "test": test, "features": names, "classes": [int(c) for c in m.classes_],
        "mean": sc.mean_.round(6).tolist(), "scale": sc.scale_.round(6).tolist(),
        "coef": m.coef_.round(6).tolist(), "intercept": m.intercept_.round(6).tolist(),
        "window_accuracy": acc}
    data.setdefault("pool", {})[key] = {"subject": yte.tolist(),
                                       "X": np.round(Xte, 4).tolist()}
    for s, start, label in SAMPLES[key]:
        idx = np.where(yte == s)[0]
        start = len(idx) // 2 if start is None else start
        sel = idx[start:start + SAMPLE_WINDOWS]
        df = pd.DataFrame(Xte[sel], columns=names).round(6)
        df.insert(0, "true_participant", s)
        fname = f"P{s:02d}_{test}_from{start * 4}s_{label.replace(' ', '-')}.csv"
        df.to_csv(OUT / "samples" / fname, index=False)
        p = m.predict_proba(sc.transform(Xte[sel]))
        samples.append({"file": fname, "model": key, "participant": s, "language": test, "label": label,
                        "csv": df.to_csv(index=False),
                        "expected_top": int(m.classes_[np.log(p + 1e-12).sum(0).argmax()])})
data["samples"] = samples


def rows(name):
    return json.loads(pd.read_csv(RES / name).to_json(orient="records"))

data["model_comparison"] = rows("model_comparison.csv")
data["test_duration"] = rows("test_evidence_duration_clustered.csv")
data["enrollment"] = rows("enrollment_duration.csv")
data["artifact"] = rows("artifact_sensitivity.csv")
data["legacy"] = rows("legacy_full_session_ica_comparison.csv")
data["per_subject"] = rows("per_subject_metrics.csv")


# ---------- one real 4-s window, shown stage by stage in the Pipeline tab ----------
import sys, mne
from scipy.signal import welch
sys.path.insert(0, str(ROOT))
from src.config import CHANNELS, BANDS, SFREQ, LINE_FREQ
mne.set_log_level("ERROR")
edf = next((ROOT / "data/raw").glob("S8-*/Hindi/S8-H-See3.edf"))
raw = mne.io.read_raw_edf(edf, preload=True).pick(CHANNELS)
raw.reorder_channels(CHANNELS)
a, b = int(20 * SFREQ), int(24 * SFREQ)
x_raw = raw.get_data()[:, a:b] * 1e6
notched = raw.copy().notch_filter([LINE_FREQ, 2 * LINE_FREQ])
filt = notched.copy().filter(1.0, 45.0)
car = filt.copy().set_eeg_reference("average")
x_filt = filt.get_data()[:, a:b] * 1e6
x_car = car.get_data()[:, a:b] * 1e6
f, P_raw = welch(raw.get_data()[:, a:b], fs=SFREQ, nperseg=int(2 * SFREQ))
_, P = welch(car.get_data()[:, a:b], fs=SFREQ, nperseg=int(2 * SFREQ))
keep = f <= 120
h = mne.filter.create_filter(None, SFREQ, 1.0, 45.0)
from scipy.signal import freqz
fw, H = freqz(h, worN=512, fs=SFREQ)
tot = P[:, (f >= 1) & (f <= 45)].sum(-1)
bp_log, bp_rel = [], []
for lo, hi in BANDS.values():
    bp = P[:, (f >= lo) & (f < hi)].sum(-1)
    bp_log.append(np.log10(bp + 1e-30).tolist()); bp_rel.append((bp / tot).tolist())
# coherence (same estimator as src/corrected_experiments.coherence_features)
W = car.get_data()[:, a:b]
nper, hop = 256, 128
taper = np.hanning(nper)
fr = np.fft.rfftfreq(nper, 1 / SFREQ)
spec = np.stack([np.fft.rfft(W[:, s:s + nper] * taper, axis=-1) for s in range(0, W.shape[1] - nper + 1, hop)], 1)
cross = np.einsum("isf,jsf->ijf", spec, spec.conj()) / spec.shape[1]
pw = np.real(np.einsum("iif->if", cross))
coh = np.abs(cross) ** 2 / (pw[:, None] * pw[None] + 1e-30)
coh_b = [coh[..., (fr >= lo) & (fr < hi)].mean(-1).round(3).tolist() for lo, hi in BANDS.values()]
ds = lambda m: np.round(m[:, ::2], 2).tolist()  # 128 Hz for drawing
data["signal"] = {"participant": 8, "file": "Hindi block, 20-24 s of chunk 3", "channels": CHANNELS,
    "bands": {k: list(v) for k, v in BANDS.items()}, "fs_plot": SFREQ / 2,
    "raw": ds(x_raw - x_raw.mean(1, keepdims=True)), "filtered": ds(x_filt), "car": ds(x_car),
    "freqs": f[keep].tolist(), "psd_raw_db": np.round(10 * np.log10(P_raw[:, keep] * 1e12 + 1e-12), 2).tolist(),
    "psd_db": np.round(10 * np.log10(P[:, keep] * 1e12 + 1e-12), 2).tolist(),
    "filter_f": fw[::2].round(2).tolist(), "filter_db": np.round(20 * np.log10(np.abs(H[::2]) + 1e-9), 2).tolist(),
    "bp_log": np.round(bp_log, 3).tolist(), "bp_rel": np.round(bp_rel, 4).tolist(), "coh": coh_b}

def conf(name):
    df = pd.read_csv(RES / name, index_col=0)
    return (df.values / df.values.sum(1, keepdims=True)).round(3).tolist()
data["confusion"] = {}
for rep in ["power", "coherence", "power_plus_coherence"]:
    for d, fn in [("Arabic->Hindi", "Arabic_to_Hindi"), ("Hindi->Arabic", "Hindi_to_Arabic")]:
        data["confusion"][f"{rep}|{d}"] = conf(f"confusion_ica_enrollment_only_{rep}_{fn}.csv")
data["macro"] = rows("participant_macro_metrics.csv")
data["paired"] = rows("paired_participant_comparisons.csv")

tpl = (OUT / "template.html").read_text(encoding="utf-8")
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\/")
(OUT / "index.html").write_text(tpl.replace("/*__DATA__*/null", blob), encoding="utf-8")
print("wrote", OUT / "index.html", f"{len(blob)/1e6:.2f} MB;",
      {k: round(v["window_accuracy"], 3) for k, v in data["models"].items()},
      [(s["file"], s["expected_top"]) for s in samples])
