"""Cache ICA-cleaned 4-s windows (same windows as the band-power features) for EEGNet/coherence.
Output: results/windows_ica.npz  (X: n_win x 14 x 1024 float32, plus metadata arrays)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from src.config import RESULTS, WINDOW_S, SFREQ
from src.data import index_files, load_subject
from src.features import preprocess

step = int(WINDOW_S * SFREQ)
files = index_files()
X, subj, lang, fid, order = [], [], [], [], []
for s, sf in files.groupby("subject"):
    data, start = preprocess(load_subject(sf), "ica").get_data(), 0
    for _, row in sf.iterrows():
        seg = data[:, start:start + int(row.n_samples)]; start += int(row.n_samples)
        n = seg.shape[1] // step
        X.append(seg[:, : n * step].reshape(seg.shape[0], n, step).transpose(1, 0, 2).astype(np.float32))
        subj += [s] * n; lang += [row.language] * n; fid += [row.file_id] * n; order += [row.order] * n
    print("subject", s, "done", flush=True)
np.savez_compressed(RESULTS / "windows_ica.npz", X=np.concatenate(X) * 1e6,  # microvolts
                    subject=np.array(subj), language=np.array(lang), file_id=np.array(fid), order=np.array(order))
print("saved", sum(len(x) for x in X), "windows")
