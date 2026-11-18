"""Option 1 paper: language-invariant EEG biometrics. Main protocol = cross-language
(train on one language block, test on the other). Pipeline/model fixed: ICA + logistic regression.

Analyses
  duration  : identification vs evidence length (average class probabilities over k windows of 4 s)
  bands     : features from one frequency band only
  regions   : features from one scalp region only
  verify    : verification EER (genuine vs impostor scores from class probabilities)
  time      : within-language, train early half of block -> test late half (temporal robustness)
Outputs: results/bio_*.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_curve
from src.config import RESULTS, BANDS
from src.evaluate import load_features, MODELS

PIPE, MODEL = "ica", "logreg"
REGIONS = {"frontal": ["FP1", "FP2", "F7", "F3", "F4", "F8"], "temporal": ["T3", "T4", "T5", "T6"],
           "parietal": ["P3", "P4"], "occipital": ["O1", "O2"]}
DIRECTIONS = [("Arabic", "Hindi"), ("Hindi", "Arabic")]

X, m, cols = load_features(PIPE)
cols = np.array(cols)
y = m.subject.to_numpy()


def fit_predict(Xf, tr, te):
    clf = MODELS[MODEL]().fit(Xf[tr], y[tr])
    return clf, clf.predict_proba(Xf[te])


def cross_language(Xf):
    accs = []
    for a, b in DIRECTIONS:
        tr, te = (m.language == a).to_numpy(), (m.language == b).to_numpy()
        clf, P = fit_predict(Xf, tr, te)
        accs.append(balanced_accuracy_score(y[te], clf.classes_[P.argmax(1)]))
    return float(np.mean(accs))


def eer(genuine, impostor):
    s = np.r_[genuine, impostor]; t = np.r_[np.ones_like(genuine), np.zeros_like(impostor)]
    fpr, tpr, _ = roc_curve(t, s)
    i = np.nanargmin(np.abs(fpr - (1 - tpr)))
    return float((fpr[i] + 1 - tpr[i]) / 2)


# duration + verification (both directions)
dur_rows, ver_rows = [], []
for a, b in DIRECTIONS:
    tr, te = (m.language == a).to_numpy(), (m.language == b).to_numpy()
    clf, P = fit_predict(X, tr, te)
    mt = m[te].reset_index(drop=True)
    for k in [1, 2, 4, 8]:                       # 4, 8, 16, 32 s of evidence
        blk = mt.groupby("file_id").cumcount() // k
        key = mt.file_id + "_" + blk.astype(str)
        Pk = pd.DataFrame(P).groupby(key.values).mean()
        yk = mt.groupby(key.values).subject.first().loc[Pk.index]
        acc = balanced_accuracy_score(yk, clf.classes_[Pk.to_numpy().argmax(1)])
        dur_rows.append(dict(direction=f"{a}->{b}", seconds=4 * k, n_tests=len(yk), bal_acc=acc))
        if k in (1, 4):
            S = Pk.to_numpy(); mask = clf.classes_[None, :] == yk.to_numpy()[:, None]
            ver_rows.append(dict(direction=f"{a}->{b}", seconds=4 * k, eer=eer(S[mask], S[~mask])))

# band and region ablations (cross-language)
abl = [dict(kind="all", subset="all", n_feat=len(cols), bal_acc=cross_language(X))]
for b in BANDS:
    sel = np.char.find(cols.astype(str), f"_{b}_") >= 0
    abl.append(dict(kind="band", subset=b, n_feat=int(sel.sum()), bal_acc=cross_language(X[:, sel])))
for r, chs in REGIONS.items():
    sel = np.array([c.split("_")[0] in chs for c in cols])
    abl.append(dict(kind="region", subset=r, n_feat=int(sel.sum()), bal_acc=cross_language(X[:, sel])))
for ftype in ["log", "rel"]:
    sel = np.char.endswith(cols.astype(str), f"_{ftype}")
    abl.append(dict(kind="feature", subset=ftype, n_feat=int(sel.sum()), bal_acc=cross_language(X[:, sel])))

# muscle (EMG) control: drop EMG-prone bands and/or EMG-prone sites (frontal-polar, temporal)
band_of = np.array([c.split("_")[1] for c in cols]); ch_of = np.array([c.split("_")[0] for c in cols])
low = np.isin(band_of, ["delta", "theta", "alpha", "beta"])      # 1-30 Hz
very_low = np.isin(band_of, ["delta", "theta", "alpha"])         # 1-13 Hz
central = ~np.isin(ch_of, ["FP1", "FP2", "F7", "F8", "T3", "T4", "T5", "T6"])
for name, sel in [("1-30 Hz", low), ("1-13 Hz", very_low), ("1-30 Hz, non-EMG sites", low & central),
                  ("1-13 Hz, non-EMG sites", very_low & central)]:
    abl.append(dict(kind="emg_control", subset=name, n_feat=int(sel.sum()), bal_acc=cross_language(X[:, sel])))

# temporal robustness within each language: early half of block -> late half
rank = m.groupby(["subject", "language"]).order.rank(method="dense")
size = m.groupby(["subject", "language"]).order.transform("nunique")
early = (rank <= size / 2).to_numpy()
time_rows = []
for lang in ["Arabic", "Hindi"]:
    L = (m.language == lang).to_numpy()
    clf, P = fit_predict(X, L & early, L & ~early)
    time_rows.append(dict(language=lang, protocol="early->late",
                          bal_acc=balanced_accuracy_score(y[L & ~early], clf.classes_[P.argmax(1)])))

for name, rows in [("duration", dur_rows), ("verification", ver_rows), ("ablation", abl), ("time", time_rows)]:
    df = pd.DataFrame(rows); df.to_csv(RESULTS / f"bio_{name}.csv", index=False)
    print(f"\n== {name}\n{df.round(3).to_string(index=False)}")
