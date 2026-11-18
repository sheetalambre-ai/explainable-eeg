"""Connectivity baseline (cf. La Rocca et al. 2014): magnitude-squared coherence between all
14 x 13 / 2 = 91 channel pairs, averaged within 5 bands -> 455 features per 4-s window.
Evaluated under the cross-language protocol alone and combined with band power.
Output: results/bio_coherence.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score
from src.config import RESULTS, BANDS, SFREQ
from src.evaluate import load_features, MODELS

NPER = 256                                         # 1-s segments, 50% overlap -> 7 per window
d = np.load(RESULTS / "windows_ica.npz")
X, files = d["X"], d["file_id"]
iu = np.triu_indices(X.shape[1], 1)
freqs = np.fft.rfftfreq(NPER, 1 / SFREQ)
win = np.hanning(NPER).astype(np.float32)
starts = range(0, X.shape[2] - NPER + 1, NPER // 2)


def coherence(chunk):
    F = np.stack([np.fft.rfft(chunk[..., s:s + NPER] * win, axis=-1) for s in starts], 2)  # w,ch,seg,f
    S = np.einsum("wisf,wjsf->wijf", F, F.conj()) / F.shape[2]
    P = np.real(np.einsum("wiif->wif", S))
    coh = np.abs(S) ** 2 / (P[:, :, None] * P[:, None] + 1e-30)
    out = [coh[:, iu[0], iu[1]][..., (freqs >= lo) & (freqs < hi)].mean(-1) for lo, hi in BANDS.values()]
    return np.concatenate(out, 1)


C = np.concatenate([coherence(X[i:i + 300]) for i in range(0, len(X), 300)])
Xp, m, _ = load_features("ica")
assert (m.file_id.to_numpy() == files).all(), "window order mismatch"
y, lang = m.subject.to_numpy(), m.language.to_numpy()

rows = []
for name, F in [("band power", Xp), ("coherence", C), ("power + coherence", np.hstack([Xp, C]))]:
    for a, b in [("Arabic", "Hindi"), ("Hindi", "Arabic")]:
        clf = MODELS["logreg"]().fit(F[lang == a], y[lang == a])
        acc = balanced_accuracy_score(y[lang == b], clf.predict(F[lang == b]))
        rows.append(dict(features=name, n_feat=F.shape[1], direction=f"{a}->{b}", bal_acc=acc))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(RESULTS / "bio_coherence.csv", index=False)
