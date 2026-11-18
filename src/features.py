"""Part A: preprocessing pipelines, quality metrics, band-power window features."""
import numpy as np
import mne
from scipy.signal import welch
from .config import BANDS, WINDOW_S, SFREQ, LINE_FREQ, SEED


def preprocess(raw: mne.io.Raw, pipeline: str) -> mne.io.Raw:
    raw = raw.copy()
    if pipeline == "raw":
        return raw
    raw.notch_filter([LINE_FREQ, 2 * LINE_FREQ])
    raw.filter(1.0, 45.0)
    raw.set_eeg_reference("average")
    if pipeline == "filtered":
        return raw
    if pipeline == "ica":
        ica = mne.preprocessing.ICA(n_components=0.99, method="fastica",
                                    random_state=SEED, max_iter=1000)
        ica.fit(raw)
        bads, _ = ica.find_bads_eog(raw, ch_name=["FP1", "FP2"])  # frontal = ocular proxy
        ica.exclude = bads
        ica.apply(raw)
        raw.info["description"] = f"ica_removed={len(bads)}"
        return raw
    raise ValueError(pipeline)


def window_features(data: np.ndarray, ch_names: list[str]) -> tuple[np.ndarray, list[str], np.ndarray]:
    """data: (n_ch, n_samples) for ONE file. Returns X (n_win, n_feat), names, quality."""
    step = int(WINDOW_S * SFREQ)
    n_win = data.shape[1] // step
    wins = data[:, : n_win * step].reshape(data.shape[0], n_win, step).transpose(1, 0, 2)
    freqs, psd = welch(wins, fs=SFREQ, nperseg=int(2 * SFREQ), axis=-1)  # (win, ch, f)
    total = psd[..., (freqs >= 1) & (freqs <= 45)].sum(-1)
    feats, names = [], []
    for b, (lo, hi) in BANDS.items():
        bp = psd[..., (freqs >= lo) & (freqs < hi)].sum(-1)
        feats += [np.log10(bp + 1e-30), bp / total]
        names += [f"{c}_{b}_log" for c in ch_names] + [f"{c}_{b}_rel" for c in ch_names]
    X = np.concatenate(feats, axis=1)
    # quality per window: peak-to-peak (uV, max over channels) and line-noise ratio
    ptp = (wins.max(-1) - wins.min(-1)).max(-1) * 1e6
    line = psd[..., np.abs(freqs - LINE_FREQ) < 1].sum(-1) / (total + 1e-30)
    quality = np.c_[ptp, line.mean(-1)]
    return X, names, quality
