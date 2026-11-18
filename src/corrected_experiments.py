"""Leakage-conscious cross-script EEG biometric experiments.

All learned transforms used by the primary ICA pipeline (ICA fit and ocular
component selection) are fitted from the enrollment language only. Test blocks
are transformed with the frozen enrollment ICA. The no-ICA filtered pipeline is
also evaluated as a sensitivity analysis.
"""
from __future__ import annotations

import os
from pathlib import Path
from ast import literal_eval

# Keep MNE and Numba configuration/cache writes inside the writable project.
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "corrected"
OUT.mkdir(parents=True, exist_ok=True)
CACHE_DIR = OUT / "feature_cache"
CACHE_DIR.mkdir(exist_ok=True)
os.environ.setdefault("_MNE_FAKE_HOME_DIR", str(OUT / "mne_home"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(OUT / "numba_cache"))
Path(os.environ["_MNE_FAKE_HOME_DIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["NUMBA_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)

import mne
import numpy as np
import pandas as pd
from scipy.signal import welch
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.covariance import LedoitWolf
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (balanced_accuracy_score, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from .config import BANDS, CHANNELS, LINE_FREQ, RESULTS, SEED, SFREQ, WINDOW_S
from .data import load_subject
from .features import preprocess, window_features

PREPROCESS_VERSION = "enrollment_ica_v1"
STEP = int(SFREQ * WINDOW_S)
N_SPLITS = 3
N_BOOT = 5000
N_PERM = 2000
N_ENROLL_REP = 10
MODEL_NAMES = ["logreg", "shrinkage_lda", "linear_svm"]
DIRECTIONS = [("Arabic", "Hindi"), ("Hindi", "Arabic")]
_leakage_loaded = []
_metric_progress = []
_subject_progress = []


class SharedMahalanobis(ClassifierMixin, BaseEstimator):
    """Nearest class mean under a Ledoit-Wolf shared covariance metric."""
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        self.classes_ = np.unique(y)
        self.means_ = np.stack([X[np.asarray(y) == c].mean(axis=0) for c in self.classes_])
        cov = LedoitWolf().fit(X).covariance_
        self.precision_ = np.linalg.pinv(cov, hermitian=True)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        # Bound memory for large held-out blocks (N x classes x features).
        predictions = []
        for start in range(0, len(X), 2048):
            batch = X[start:start + 2048]
            delta = batch[:, None, :] - self.means_[None, :, :]
            d2 = np.einsum("ncd,de,nce->nc", delta, self.precision_, delta, optimize=True)
            predictions.append(self.classes_[np.argmin(d2, axis=1)])
        return np.concatenate(predictions)


def file_path_map(raw_dir: Path) -> dict[str, str]:
    return {p.name: str(p) for p in raw_dir.rglob("*.edf")}


def make_windows(raw: mne.io.BaseRaw, files: pd.DataFrame, language: str):
    """Extract per-file, non-overlapping windows without crossing EDF boundaries."""
    if list(raw.ch_names) != CHANNELS:
        raise RuntimeError(f"Channel order mismatch: {raw.ch_names} != {CHANNELS}")
    Xs, W, rows = [], [], []
    cursor = 0
    names = None
    for _, fr in files.sort_values("order").iterrows():
        nsamp = int(fr.n_samples)
        seg = raw.get_data(start=cursor, stop=cursor + nsamp, picks=CHANNELS)
        cursor += nsamp
        n_win = seg.shape[1] // STEP
        if n_win == 0:
            continue
        wins = seg[:, :n_win * STEP].reshape(len(CHANNELS), n_win, STEP).transpose(1, 0, 2)
        F, names, _ = window_features(seg, CHANNELS)
        Xs.append(F.astype(np.float32))
        W.append(wins.astype(np.float32))
        meta = pd.DataFrame({
            "subject": int(fr.subject), "native": str(fr.native), "sex": str(fr.sex),
            "language": language, "file_id": str(fr.file_id), "order": int(fr.order),
            "window": np.arange(n_win),
        })
        rows.append(meta)
    if cursor != raw.n_times:
        raise RuntimeError(f"EDF sample accounting mismatch: files={cursor}, raw={raw.n_times}")
    return np.concatenate(Xs), np.concatenate(W), pd.concat(rows, ignore_index=True), names


def coherence_features(W: np.ndarray) -> np.ndarray:
    """Five-band magnitude-squared coherence for 91 channel pairs per window."""
    nper, hop = 256, 128
    starts = range(0, STEP - nper + 1, hop)
    taper = np.hanning(nper).astype(np.float32)
    freq = np.fft.rfftfreq(nper, 1 / SFREQ)
    iu = np.triu_indices(W.shape[1], 1)
    spectra = np.stack([np.fft.rfft(W[..., s:s+nper] * taper, axis=-1) for s in starts], axis=2)
    cross = np.einsum("wisf,wjsf->wijf", spectra, spectra.conj(), optimize=True) / spectra.shape[2]
    power = np.real(np.einsum("wiif->wif", cross, optimize=True))
    coh = np.abs(cross) ** 2 / (power[:, :, None, :] * power[:, None, :, :] + 1e-30)
    return np.concatenate([
        coh[:, iu[0], iu[1]][..., (freq >= lo) & (freq < hi)].mean(axis=-1)
        for lo, hi in BANDS.values()
    ], axis=1).astype(np.float32)


def preprocess_language(files: pd.DataFrame) -> mne.io.BaseRaw:
    raw = load_subject(files.sort_values("order"))
    return preprocess(raw, "filtered")


def fit_enrollment_ica(train_raw: mne.io.BaseRaw, test_raw: mne.io.BaseRaw):
    """Fit ICA and select ocular components on enrollment data only."""
    if list(train_raw.ch_names) != list(test_raw.ch_names) or list(train_raw.ch_names) != CHANNELS:
        raise RuntimeError("Enrollment/test channel order or channel set differs")
    ica = mne.preprocessing.ICA(n_components=0.99, method="fastica", random_state=SEED, max_iter=1000)
    ica.fit(train_raw.copy(), verbose="ERROR")
    excluded, scores = ica.find_bads_eog(train_raw.copy(), ch_name=["FP1", "FP2"], verbose="ERROR")
    ica.exclude = list(excluded)
    train_clean = ica.apply(train_raw.copy(), verbose="ERROR")
    test_clean = ica.apply(test_raw.copy(), verbose="ERROR")
    report = {"n_components": int(ica.n_components_), "excluded_components": ";".join(map(str, excluded)),
              "n_excluded": len(excluded), "eog_score_count": len(np.asarray(scores).ravel()),
              "fit_samples": int(train_raw.n_times), "test_samples_transformed": int(test_raw.n_times),
              "fit_scope": "enrollment_language_only", "test_refit": False,
              "channel_order": ";".join(train_raw.ch_names)}
    return train_clean, test_clean, report


def per_subject_metrics(y_true, y_pred, classes):
    pr, rc, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=classes, zero_division=0)
    return pd.DataFrame({"subject": classes, "precision": pr, "recall": rc, "f1": f1})


def folds_by_file(meta: pd.DataFrame):
    """Cyclic file-level folds within each subject; every class stays in every fit fold."""
    file_fold = {}
    for subject, g in meta.groupby("subject"):
        file_ids = (g[["file_id", "order"]].drop_duplicates().sort_values("order").file_id.tolist())
        if len(file_ids) < N_SPLITS:
            raise RuntimeError(f"Subject {subject} has only {len(file_ids)} enrollment files; need {N_SPLITS}")
        for rank, fid in enumerate(file_ids):
            file_fold[fid] = rank % N_SPLITS
    return np.array([file_fold[f] for f in meta.file_id])


def configs_for(name: str):
    if name == "logreg":
        return [{"C": c} for c in [0.01, 0.1, 1.0, 10.0]]
    if name == "shrinkage_lda":
        return [{"shrinkage": v} for v in ["auto", 0.1, 0.5, 0.9]]
    if name == "linear_svm":
        return [{"C": c} for c in [0.1, 1.0]]
    if name == "nearest_centroid":
        return [{"metric": m} for m in ["euclidean", "manhattan"]]
    if name == "mahalanobis":
        return [{}]
    raise ValueError(name)


def build_model(name: str, params: dict):
    if name == "logreg":
        model = LogisticRegression(C=params["C"], max_iter=3000, random_state=SEED)
    elif name == "shrinkage_lda":
        model = LinearDiscriminantAnalysis(solver="lsqr", shrinkage=params["shrinkage"])
    elif name == "linear_svm":
        model = LinearSVC(C=params["C"], dual=False, max_iter=10000, random_state=SEED)
    elif name == "nearest_centroid":
        from sklearn.neighbors import NearestCentroid
        model = NearestCentroid(metric=params["metric"])
    elif name == "mahalanobis":
        model = SharedMahalanobis()
    else:
        raise ValueError(name)
    return make_pipeline(StandardScaler(), model)


def nested_fit_predict(name, Xtr, ytr, mtr, Xte):
    fold_ids = folds_by_file(mtr)
    tuning = []
    with threadpool_limits(limits=1):
        for params in configs_for(name):
            fold_scores = []
            for fold in range(N_SPLITS):
                fit = fold_ids != fold
                val = fold_ids == fold
                model = build_model(name, params).fit(Xtr[fit], ytr[fit])
                fold_scores.append(balanced_accuracy_score(ytr[val], model.predict(Xtr[val])))
            tuning.append((float(np.mean(fold_scores)), params, fold_scores))
        best_score, best_params, best_folds = max(tuning, key=lambda x: x[0])
        model = build_model(name, best_params).fit(Xtr, ytr)
        pred = model.predict(Xte)
    return model, pred, best_params, best_score, best_folds


def read_feature_cache(path: Path):
    with np.load(path, allow_pickle=True) as d:
        version = str(d["cache_version"].item())
        if version != PREPROCESS_VERSION:
            raise RuntimeError(f"Stale corrected feature cache {path}: {version}")
        meta = pd.DataFrame({k: d[k] for k in ["subject", "native", "sex", "language", "file_id", "order", "window"]})
        meta["subject"] = meta.subject.astype(int)
        meta["order"] = meta.order.astype(int)
        meta["window"] = meta.window.astype(int)
        names = d["feature_names"].astype(str).tolist()
        result = (d["power"].copy(), meta, names, d["coherence"].copy())
        extras = {k: d[k].item() for k in ["fit_language", "ica_n_components", "ica_excluded_components",
                                             "ica_fit_samples", "test_samples_transformed", "test_refit", "channel_order"]
                  if k in d.files}
    return result, extras


def load_cached_features():
    """Load only version-matched training-only caches and reconstruct the ICA audit."""
    expected = []
    for s in range(1, 21):
        for lang in ["Arabic", "Hindi"]:
            expected.append(CACHE_DIR / f"filtered_s{s:02d}_{lang}.npz")
        for fit_lang in ["Arabic", "Hindi"]:
            for lang in ["Arabic", "Hindi"]:
                expected.append(CACHE_DIR / f"ica_{fit_lang}_s{s:02d}_{lang}.npz")
    if not all(p.is_file() for p in expected):
        return None
    for s in range(1, 21):
        for lang in ["Arabic", "Hindi"]:
            record, _ = read_feature_cache(CACHE_DIR / f"filtered_s{s:02d}_{lang}.npz")
            _CACHE[("filtered", lang)].append(record)
        for fit_lang in ["Arabic", "Hindi"]:
            other_lang = "Hindi" if fit_lang == "Arabic" else "Arabic"
            train_rec, report = read_feature_cache(CACHE_DIR / f"ica_{fit_lang}_s{s:02d}_{fit_lang}.npz")
            test_rec, _ = read_feature_cache(CACHE_DIR / f"ica_{fit_lang}_s{s:02d}_{other_lang}.npz")
            _CACHE[(f"ica_trainonly:{fit_lang}->{other_lang}", fit_lang)].append(train_rec)
            _CACHE[(f"ica_trainonly:{fit_lang}->{other_lang}", other_lang)].append(test_rec)
            _leakage_loaded.append({"subject": s, "direction": f"{fit_lang}->{other_lang}",
                                    "train_language": fit_lang, "test_language": other_lang,
                                    "n_components": report.get("ica_n_components", "not_recorded"),
                                    "excluded_components": report.get("ica_excluded_components", "not_recorded"),
                                    "n_excluded": len(str(report.get("ica_excluded_components", "")).split(";"))
                                    if report.get("ica_excluded_components", "") else 0,
                                    "fit_samples": report.get("ica_fit_samples", "not_recorded"),
                                    "test_samples_transformed": report.get("test_samples_transformed", "not_recorded"),
                                    "fit_scope": "enrollment_language_only", "test_refit": False,
                                    "channel_order": report.get("channel_order", ";".join(CHANNELS))})
    return _leakage_loaded


def subject_bootstrap(values: np.ndarray, rng) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    draws = values[rng.integers(0, len(values), size=(N_BOOT, len(values)))].mean(axis=1)
    return float(values.mean()), float(np.quantile(draws, .025)), float(np.quantile(draws, .975))


def subject_permutation_p(y_true, y_pred, meta_test, observed, rng):
    """Permute test identity labels by participant, never by EEG window."""
    subjects = np.sort(meta_test.subject.unique())
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        perm = rng.permutation(subjects)
        mapping = dict(zip(subjects, perm))
        yp = np.array([mapping[int(s)] for s in meta_test.subject])
        null[i] = balanced_accuracy_score(yp, y_pred)
    p = (1 + np.sum(null >= observed)) / (1 + N_PERM)
    return float(p), null


def evaluate_direction(direction, pipeline, representation, X, meta, feat_names, coherence):
    train_lang, test_lang = direction
    tr, te = meta.language.eq(train_lang).to_numpy(), meta.language.eq(test_lang).to_numpy()
    mtr, mte = meta.loc[tr].reset_index(drop=True), meta.loc[te].reset_index(drop=True)
    if representation == "power":
        F = X
    elif representation == "coherence":
        F = coherence
    elif representation == "power_plus_coherence":
        F = np.hstack([X, coherence])
    else:
        raise ValueError(representation)
    Xtr, Xte = F[tr], F[te]
    ytr, yte = mtr.subject.to_numpy(), mte.subject.to_numpy()
    classes = np.sort(np.unique(ytr))
    rng = np.random.default_rng(SEED)
    metric_rows, subject_rows, pred_cache = [], [], {}
    lr_model = None
    lr_params = None
    model_names = MODEL_NAMES if representation == "power" else ["logreg"]
    for model_name in model_names:
        model, pred, params, cv_mean, cv_folds = nested_fit_predict(model_name, Xtr, ytr, mtr, Xte)
        per = per_subject_metrics(yte, pred, classes)
        mean, lo, hi = subject_bootstrap(per.recall.to_numpy(), rng)
        acc = float(balanced_accuracy_score(yte, pred))
        p = np.nan
        if model_name == "logreg" and pipeline == "ica_enrollment_only" and representation == "power":
            p, _ = subject_permutation_p(yte, pred, mte, acc, rng)
        metric_rows.append({"direction": f"{train_lang}->{test_lang}", "preprocessing": pipeline,
                            "representation": representation, "model": model_name,
                            "n_features": F.shape[1], "balanced_accuracy": acc,
                            "subject_bootstrap_mean": mean, "ci95_low": lo, "ci95_high": hi,
                            "nested_cv_balanced_accuracy": cv_mean,
                            "nested_cv_fold_scores": ";".join(f"{v:.6f}" for v in cv_folds),
                            "selected_parameters": str(params), "subject_permutation_p": p})
        per["direction"] = f"{train_lang}->{test_lang}"
        per["preprocessing"] = pipeline
        per["representation"] = representation
        per["model"] = model_name
        subject_rows.append(per)
        _metric_progress.extend(metric_rows[-1:])
        _subject_progress.append(per)
        pd.DataFrame(_metric_progress).to_csv(OUT / "model_comparison_progress.csv", index=False)
        pd.concat(_subject_progress, ignore_index=True).to_csv(OUT / "per_subject_progress.csv", index=False)
        pred_cache[model_name] = (pred, per.recall.to_numpy())
        if model_name == "logreg":
            lr_model, lr_params = model, params
        cm = confusion_matrix(yte, pred, labels=classes)
        if model_name == "logreg":
            pd.DataFrame(cm, index=classes, columns=classes).to_csv(
                OUT / f"confusion_{pipeline}_{representation}_{train_lang}_to_{test_lang}.csv")
        print(f"  {pipeline} {representation} {train_lang}->{test_lang} {model_name}: {acc:.4f}", flush=True)

    enroll_rows, duration_rows = [], []
    if representation == "power":
        # Enrollment-duration curve uses the training-block selected C. Each point averages
        # repeated, class-balanced enrollment subsamples; the test set stays fixed.
        C = float(lr_params["C"])
        groups = {int(s): np.flatnonzero(ytr == s) for s in classes}
        limits = min(map(len, groups.values()))
        durations = sorted(set([1, 2, 4, 8, 16, 32, 64, limits]))
        durations = [n for n in durations if n <= limits]
        rng_enroll = np.random.default_rng(SEED + 1)
        for n in durations:
            recalls = []
            for rep in range(N_ENROLL_REP):
                chosen = np.concatenate([rng_enroll.choice(groups[s], size=n, replace=False) for s in classes])
                clf = build_model("logreg", {"C": C}).fit(Xtr[chosen], ytr[chosen])
                pred_n = clf.predict(Xte)
                per_n = per_subject_metrics(yte, pred_n, classes)
                recalls.append(per_n.recall.to_numpy())
            subject_means = np.mean(np.stack(recalls), axis=0)
            mean, lo, hi = subject_bootstrap(subject_means, rng_enroll)
            enroll_rows.append({"direction": f"{train_lang}->{test_lang}", "preprocessing": pipeline,
                                "representation": representation, "enrollment_windows_per_subject": n,
                                "median_enrollment_seconds_per_subject": 4 * n,
                                "repetitions": N_ENROLL_REP, "balanced_accuracy": mean,
                                "ci95_low": lo, "ci95_high": hi, "test_window_seconds": 4})

        # Test evidence duration is distinct from enrollment duration.
        probs = lr_model.predict_proba(Xte)
        for k in [1, 2, 4, 8]:
            tm = mte.copy()
            tm["block"] = tm.groupby("file_id").cumcount() // k
            probs_df = pd.DataFrame(probs, columns=lr_model[-1].classes_)
            probs_df["file_id"] = tm.file_id.to_numpy()
            probs_df["block"] = tm.block.to_numpy()
            avg = probs_df.groupby(["file_id", "block"], sort=False).mean()
            key = tm.groupby(["file_id", "block"], sort=False).subject.first()
            yy = key.loc[avg.index].to_numpy()
            pred_d = lr_model[-1].classes_[avg.to_numpy().argmax(axis=1)]
            duration_rows.append({"direction": f"{train_lang}->{test_lang}", "preprocessing": pipeline,
                                  "representation": representation, "test_evidence_seconds": 4 * k,
                                  "n_test_segments": len(yy), "balanced_accuracy": balanced_accuracy_score(yy, pred_d)})

    return metric_rows, subject_rows, enroll_rows, duration_rows, pred_cache


def corrected_ablation(X, meta, names, coherence, direction, pipeline):
    train_lang, test_lang = direction
    tr, te = meta.language.eq(train_lang).to_numpy(), meta.language.eq(test_lang).to_numpy()
    ytr, yte = meta.loc[tr, "subject"].to_numpy(), meta.loc[te, "subject"].to_numpy()
    cols = np.asarray(names)
    band = np.array([c.split("_")[1] for c in cols])
    channel = np.array([c.split("_")[0] for c in cols])
    safe_ch = np.isin(channel, ["F3", "F4", "P3", "P4", "O1", "O2"])
    selections = {
        "all_power": np.ones(len(cols), dtype=bool),
        "1_13_hz_all_channels": np.isin(band, ["delta", "theta", "alpha"]),
        "1_30_hz_all_channels": np.isin(band, ["delta", "theta", "alpha", "beta"]),
        "1_13_hz_restricted_sites": np.isin(band, ["delta", "theta", "alpha"]) & safe_ch,
        "1_30_hz_restricted_sites": np.isin(band, ["delta", "theta", "alpha", "beta"]) & safe_ch,
    }
    rows = []
    for name, sel in selections.items():
        model, pred, params, cv, _ = nested_fit_predict("logreg", X[tr][:, sel], ytr,
                                                        meta.loc[tr].reset_index(drop=True),
                                                        X[te][:, sel])
        per = per_subject_metrics(yte, pred, np.sort(np.unique(ytr)))
        mean, lo, hi = subject_bootstrap(per.recall.to_numpy(), np.random.default_rng(SEED))
        rows.append({"direction": f"{train_lang}->{test_lang}", "preprocessing": pipeline,
                     "ablation": name, "n_features": int(sel.sum()),
                     "balanced_accuracy": balanced_accuracy_score(yte, pred), "subject_mean": mean,
                     "ci95_low": lo, "ci95_high": hi, "nested_cv_balanced_accuracy": cv})
    return rows


def evaluate_feature_caches(leakage):
    all_metrics, all_subjects, all_enrollment, all_duration, all_ablation = [], [], [], [], []
    pd.DataFrame(leakage).to_csv(OUT / "leakage_audit.csv", index=False)
    print("starting nested model comparisons", flush=True)
    with threadpool_limits(limits=1):
        _evaluate_feature_caches_inner(leakage, all_metrics, all_subjects, all_enrollment, all_duration, all_ablation)


def _evaluate_feature_caches_inner(leakage, all_metrics, all_subjects, all_enrollment, all_duration, all_ablation):
    for pipeline_name in ["filtered", "ica_trainonly:Arabic->Hindi", "ica_trainonly:Hindi->Arabic"]:
        parts = []
        for language in ["Arabic", "Hindi"]:
            parts.extend(_CACHE[(pipeline_name, language)])
        X = np.concatenate([r[0] for r in parts])
        meta = pd.concat([r[1] for r in parts], ignore_index=True)
        coh = np.concatenate([r[3] for r in parts])
        names = parts[0][2]
        for train_lang, test_lang in DIRECTIONS:
            if pipeline_name.startswith("ica_trainonly:") and pipeline_name != f"ica_trainonly:{train_lang}->{test_lang}":
                continue
            label = "filtered_no_ica" if pipeline_name == "filtered" else "ica_enrollment_only"
            out_metrics, out_subject, out_enroll, out_dur, _ = evaluate_direction(
                (train_lang, test_lang), label, "power", X, meta, names, coh)
            for rep in ["coherence", "power_plus_coherence"]:
                met, sub, _, _, _ = evaluate_direction((train_lang, test_lang), label, rep, X, meta, names, coh)
                out_metrics.extend(met); out_subject.extend(sub)
            all_metrics.extend(out_metrics); all_subjects.extend(out_subject)
            all_enrollment.extend(out_enroll); all_duration.extend(out_dur)
            if label == "ica_enrollment_only":
                all_ablation.extend(corrected_ablation(X, meta, names, coh, (train_lang, test_lang), label))
            pd.DataFrame(all_metrics).to_csv(OUT / "model_comparison.csv", index=False)
            pd.concat(all_subjects, ignore_index=True).to_csv(OUT / "per_subject_metrics.csv", index=False)
            pd.DataFrame(all_enrollment).to_csv(OUT / "enrollment_duration.csv", index=False)
            pd.DataFrame(all_duration).to_csv(OUT / "test_evidence_duration.csv", index=False)
            pd.DataFrame(all_ablation).to_csv(OUT / "artifact_sensitivity.csv", index=False)
            print(f"completed {label} {train_lang}->{test_lang}", flush=True)
    print("corrected experiments complete", OUT, flush=True)


def run():
    mne.set_log_level("ERROR")
    cached_audit = load_cached_features()
    if cached_audit is not None:
        print("loaded version-matched enrollment-only caches", flush=True)
        evaluate_feature_caches(cached_audit)
        return

    idx_path = RESULTS / "file_index.csv"
    idx = pd.read_csv(idx_path)
    from .config import RAW_DIR
    by_subject_order = {}
    for p in RAW_DIR.rglob("*.edf"):
        m = __import__("re").search(r"S(\d+)-.*?([AH])-See(\d+)\.edf$", p.name, flags=__import__("re").I)
        if not m:
            continue
        subject = int(m.group(1)); lang = {"A": "Arabic", "H": "Hindi"}[m.group(2).upper()]
        chunk = int(m.group(3))
        by_subject_order[(subject, lang, chunk)] = str(p)
    idx["path"] = idx.apply(lambda r: by_subject_order[(int(r.subject), str(r.language), int(r.chunk))], axis=1)
    leakage = []

    for subject, sf in idx.groupby("subject", sort=True):
        print(f"starting preprocessing subject {subject}", flush=True)
        lang_raw = {}
        lang_data = {}
        for language in ["Arabic", "Hindi"]:
            fs = sf[sf.language.eq(language)].sort_values("order")
            print(f"  loading/filtering subject {subject} {language}", flush=True)
            raw = preprocess_language(fs)
            lang_raw[language] = raw
            power, wins, meta, names = make_windows(raw, fs, language)
            conn = coherence_features(wins)
            lang_data[language] = (power, wins, meta, names, conn)
            cache_name = CACHE_DIR / f"filtered_s{int(subject):02d}_{language}.npz"
            np.savez_compressed(cache_name, power=power, coherence=conn,
                                subject=meta.subject.to_numpy(), native=meta.native.to_numpy(),
                                sex=meta.sex.to_numpy(), language=meta.language.to_numpy(),
                                file_id=meta.file_id.to_numpy(), order=meta.order.to_numpy(),
                                window=meta.window.to_numpy(), feature_names=np.asarray(names),
                                cache_version=PREPROCESS_VERSION, fit_language="none_fixed_filter")

        # Filtered/no-ICA pipeline: identical fixed filtering, no cross-block fit.
        for language in ["Arabic", "Hindi"]:
            power, wins, meta, names, conn = lang_data[language]
            # Accumulate separately after loop below using per-direction stack helper.

        for train_lang, test_lang in DIRECTIONS:
            print(f"  fitting ICA subject {subject}, fit block {train_lang}", flush=True)
            train_raw, test_raw, report = fit_enrollment_ica(lang_raw[train_lang], lang_raw[test_lang])
            report.update({"subject": int(subject), "direction": f"{train_lang}->{test_lang}",
                           "train_language": train_lang, "test_language": test_lang})
            leakage.append(report)
            for language, raw_clean in [(train_lang, train_raw), (test_lang, test_raw)]:
                fs = sf[sf.language.eq(language)].sort_values("order")
                power, wins, meta, names = make_windows(raw_clean, fs, language)
                conn = coherence_features(wins)
                # Keep only features and metadata in memory; raw windows are discarded.
                key = (f"ica_trainonly:{train_lang}->{test_lang}", language)
                _CACHE[key].append((power, meta, names, conn))
                cache_name = CACHE_DIR / f"ica_{train_lang}_s{int(subject):02d}_{language}.npz"
                np.savez_compressed(cache_name, power=power, coherence=conn,
                                    subject=meta.subject.to_numpy(), native=meta.native.to_numpy(),
                                    sex=meta.sex.to_numpy(), language=meta.language.to_numpy(),
                                    file_id=meta.file_id.to_numpy(), order=meta.order.to_numpy(),
                                    window=meta.window.to_numpy(), feature_names=np.asarray(names),
                                    cache_version=PREPROCESS_VERSION, fit_language=train_lang,
                                    ica_n_components=report["n_components"],
                                    ica_excluded_components=report["excluded_components"],
                                    ica_fit_samples=report["fit_samples"],
                                    test_samples_transformed=report["test_samples_transformed"],
                                    test_refit=report["test_refit"],
                                    channel_order=report["channel_order"])
                print(f"  saved ICA features subject {subject}, fit {train_lang}, block {language}", flush=True)
            print(f"preprocessed subject {subject} for {train_lang}->{test_lang}", flush=True)
        for language in ["Arabic", "Hindi"]:
            power, wins, meta, names, conn = lang_data[language]
            _CACHE[("filtered", language)].append((power, meta, names, conn))
        pd.DataFrame(leakage).to_csv(OUT / "leakage_audit.csv", index=False)

    evaluate_feature_caches(leakage)


_CACHE: dict[tuple[str, str], list] = {}
for _key in [("filtered", "Arabic"), ("filtered", "Hindi"),
             ("ica_trainonly:Arabic->Hindi", "Arabic"), ("ica_trainonly:Arabic->Hindi", "Hindi"),
             ("ica_trainonly:Hindi->Arabic", "Arabic"), ("ica_trainonly:Hindi->Arabic", "Hindi")]:
    _CACHE[_key] = []


if __name__ == "__main__":
    run()
