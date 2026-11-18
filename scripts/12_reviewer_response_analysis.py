"""Participant-clustered subgroup, paired-model, and full-session ICA analyses.

Reads the completed corrected per-participant outputs and existing full-session
ICA feature cache. All inferential summaries use people, not windows, as units.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import NATIVE, SEX, RESULTS, SEED
from src.corrected_experiments import (load_cached_features, nested_fit_predict,
                                       per_subject_metrics, _CACHE)
from src.evaluate import load_features

OUT = RESULTS / "corrected"
RNG = np.random.default_rng(SEED + 812)
N_BOOT = 10000
SUBJECTS = np.arange(1, 21)
CLASSES = SUBJECTS.copy()


def add_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["native_language"] = out.subject.map(NATIVE)
    out["sex_group"] = out.subject.map(SEX)
    out["nationality_cohort"] = out.native_language.map({"Arabic": "Yemeni", "Hindi": "Indian"})
    return out


def boot_ci(values: np.ndarray) -> tuple[float, float, float]:
    values = np.asarray(values, float)
    means = values[RNG.integers(0, len(values), size=(N_BOOT, len(values)))].mean(axis=1)
    return float(values.mean()), float(np.quantile(means, .025)), float(np.quantile(means, .975))


def holm(p_values):
    p_values = np.asarray(p_values, float)
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), float)
    running = 0.0
    for rank, ix in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[ix])
        adjusted[ix] = min(1.0, running)
    return adjusted


def legacy_full_session_ica():
    """Re-evaluate the old full-session ICA features under the corrected classifier protocol."""
    X, meta, feature_names = load_features("ica")
    rows, subjects_rows, paired_rows = [], [], []
    for train_lang, test_lang in [("Arabic", "Hindi"), ("Hindi", "Arabic")]:
        tr = meta.language.eq(train_lang).to_numpy()
        te = meta.language.eq(test_lang).to_numpy()
        mtr = meta.loc[tr].reset_index(drop=True)
        mte = meta.loc[te].reset_index(drop=True)
        model, pred, params, cv, folds = nested_fit_predict(
            "logreg", X[tr], mtr.subject.to_numpy(), mtr, X[te])
        per = per_subject_metrics(mte.subject.to_numpy(), pred, CLASSES)
        per["direction"] = f"{train_lang}->{test_lang}"
        per["preprocessing"] = "legacy_full_session_ica"
        per["representation"] = "power"
        per["model"] = "logreg"
        per = add_cohorts(per)
        subjects_rows.append(per)
        ba, lo, hi = boot_ci(per.recall.to_numpy())
        f1, f1lo, f1hi = boot_ci(per.f1.to_numpy())
        rows.append({"direction": f"{train_lang}->{test_lang}",
                     "preprocessing": "legacy_full_session_ica",
                     "representation": "power", "model": "logreg",
                     "balanced_accuracy": ba, "ba_ci95_low": lo, "ba_ci95_high": hi,
                     "macro_f1": f1, "macro_f1_ci95_low": f1lo, "macro_f1_ci95_high": f1hi,
                     "nested_cv_balanced_accuracy": cv, "selected_parameters": str(params),
                     "test_transform_fit_scope": "both language blocks (test-distribution exposure)",
                     "n_features": len(feature_names)})
        cm = confusion_matrix(mte.subject.to_numpy(), pred, labels=CLASSES)
        np.savetxt(OUT / f"confusion_legacy_full_session_ica_{train_lang}_to_{test_lang}.csv",
                   cm, delimiter=",", fmt="%d")
        row_sums = cm.sum(axis=1, keepdims=True)
        np.savetxt(OUT / f"confusion_legacy_full_session_ica_normalized_{train_lang}_to_{test_lang}.csv",
                   cm / np.maximum(row_sums, 1), delimiter=",", fmt="%.6f")
    pd.DataFrame(rows).to_csv(OUT / "legacy_full_session_ica_comparison.csv", index=False)
    legacy_per = pd.concat(subjects_rows, ignore_index=True)
    legacy_per.to_csv(OUT / "legacy_full_session_ica_per_subject.csv", index=False)
    return legacy_per


def clustered_test_duration():
    """Recompute duration scores and participant-level CIs from frozen ICA caches."""
    if not load_cached_features():
        raise RuntimeError("Missing version-matched corrected ICA caches")
    summaries, participant_rows = [], []
    for train_lang, test_lang in [("Arabic", "Hindi"), ("Hindi", "Arabic")]:
        pipe = f"ica_trainonly:{train_lang}->{test_lang}"
        parts = [record for language in ["Arabic", "Hindi"] for record in _CACHE[(pipe, language)]]
        X = np.concatenate([r[0] for r in parts])
        meta = pd.concat([r[1] for r in parts], ignore_index=True)
        train = meta.language.eq(train_lang).to_numpy()
        test = meta.language.eq(test_lang).to_numpy()
        mtr, mte = meta.loc[train].reset_index(drop=True), meta.loc[test].reset_index(drop=True)
        model, _, _, _, _ = nested_fit_predict("logreg", X[train], mtr.subject.to_numpy(), mtr, X[test])
        probabilities = model.predict_proba(X[test])
        for k in [1, 2, 4, 8]:
            tm = mte.copy()
            tm["block"] = tm.groupby("file_id", sort=False).cumcount() // k
            score = pd.DataFrame(probabilities, columns=model[-1].classes_)
            score["file_id"] = tm.file_id.to_numpy()
            score["block"] = tm.block.to_numpy()
            avg = score.groupby(["file_id", "block"], sort=False).mean()
            truth = tm.groupby(["file_id", "block"], sort=False).subject.first().loc[avg.index].to_numpy()
            prediction = model[-1].classes_[avg.to_numpy().argmax(axis=1)]
            per = per_subject_metrics(truth, prediction, CLASSES)
            per["direction"] = f"{train_lang}->{test_lang}"
            per["test_evidence_seconds"] = 4 * k
            participant_rows.append(per)
            ba, lo, hi = boot_ci(per.recall.to_numpy())
            f1, f1lo, f1hi = boot_ci(per.f1.to_numpy())
            summaries.append({"direction": f"{train_lang}->{test_lang}", "test_evidence_seconds": 4*k,
                              "n_participants": 20, "n_segments": len(truth),
                              "balanced_accuracy": ba, "ba_ci95_low": lo, "ba_ci95_high": hi,
                              "macro_f1": f1, "macro_f1_ci95_low": f1lo,
                              "macro_f1_ci95_high": f1hi})
    pd.DataFrame(summaries).to_csv(OUT / "test_evidence_duration_clustered.csv", index=False)
    pd.concat(participant_rows, ignore_index=True).to_csv(OUT / "test_evidence_duration_per_subject.csv", index=False)


def confusion_figure():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), constrained_layout=True)
    for ax, train, test, title in [(axes[0], "Arabic", "Hindi", "Arabic $\\to$ Hindi"),
                                   (axes[1], "Hindi", "Arabic", "Hindi $\\to$ Arabic")]:
        p = OUT / f"confusion_ica_enrollment_only_power_normalized_{train}_to_{test}.csv"
        cm = np.loadtxt(p, delimiter=",")
        im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1, interpolation="nearest")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Predicted identity", fontsize=8)
        ax.set_ylabel("True identity", fontsize=8)
        ax.set_xticks([0, 4, 9, 14, 19], [1, 5, 10, 15, 20], fontsize=6)
        ax.set_yticks([0, 4, 9, 14, 19], [1, 5, 10, 15, 20], fontsize=6)
        ax.axvline(9.5, color="#d55e00", lw=.7, ls="--")
        ax.axhline(9.5, color="#d55e00", lw=.7, ls="--")
    fig.colorbar(im, ax=axes, shrink=.82, label="Row-normalized recall")
    fig.savefig(OUT / "confusion_primary_directions.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main():
    corrected = pd.read_csv(OUT / "per_subject_metrics.csv")
    corrected = add_cohorts(corrected)
    legacy = legacy_full_session_ica()
    all_per = pd.concat([corrected, legacy], ignore_index=True)

    # Overall macro-F1 and cohort/sex stratification, always resampling participants.
    keys = ["direction", "preprocessing", "representation", "model"]
    overall_rows, group_rows = [], []
    for key, group in all_per.groupby(keys, sort=True):
        ba, lo, hi = boot_ci(group.recall.to_numpy())
        f1, f1lo, f1hi = boot_ci(group.f1.to_numpy())
        overall_rows.append(dict(zip(keys, key)) | {
            "n_participants": group.subject.nunique(), "balanced_accuracy": ba,
            "ba_ci95_low": lo, "ba_ci95_high": hi, "macro_f1": f1,
            "macro_f1_ci95_low": f1lo, "macro_f1_ci95_high": f1hi})
        for group_field in ["native_language", "sex_group"]:
            for cohort, sub in group.groupby(group_field, sort=True):
                sba, sblo, sbhi = boot_ci(sub.recall.to_numpy())
                sf1, sf1lo, sf1hi = boot_ci(sub.f1.to_numpy())
                group_rows.append(dict(zip(keys, key)) | {
                    "grouping": group_field, "cohort": cohort,
                    "n_participants": sub.subject.nunique(), "balanced_accuracy": sba,
                    "ba_ci95_low": sblo, "ba_ci95_high": sbhi, "macro_f1": sf1,
                    "macro_f1_ci95_low": sf1lo, "macro_f1_ci95_high": sf1hi})
    pd.DataFrame(overall_rows).to_csv(OUT / "participant_macro_metrics.csv", index=False)
    pd.DataFrame(group_rows).to_csv(OUT / "group_aware_performance.csv", index=False)

    # Primary cohort comparison: Arabic-native vs Hindi-native, separately by direction.
    cohort_rows = []
    for direction in ["Arabic->Hindi", "Hindi->Arabic"]:
        sub = corrected[(corrected.direction == direction) &
                        (corrected.preprocessing == "ica_enrollment_only") &
                        (corrected.representation == "power") & (corrected.model == "logreg")]
        for metric in ["recall", "f1"]:
            a = sub.loc[sub.native_language.eq("Arabic"), metric].to_numpy()
            h = sub.loc[sub.native_language.eq("Hindi"), metric].to_numpy()
            ba, alo, ahi = boot_ci(a); bh, hlo, hhi = boot_ci(h)
            diff = a.mean() - h.mean()
            draws_a = a[RNG.integers(0, len(a), size=(N_BOOT, len(a)))].mean(axis=1)
            draws_h = h[RNG.integers(0, len(h), size=(N_BOOT, len(h)))].mean(axis=1)
            dd = draws_a - draws_h
            cohort_rows.append({"direction": direction, "metric": metric,
                                "arabic_native_n": len(a), "arabic_native_mean": ba,
                                "arabic_native_ci95_low": alo, "arabic_native_ci95_high": ahi,
                                "hindi_native_n": len(h), "hindi_native_mean": bh,
                                "hindi_native_ci95_low": hlo, "hindi_native_ci95_high": hhi,
                                "difference_arabic_minus_hindi": diff,
                                "difference_ci95_low": np.quantile(dd, .025),
                                "difference_ci95_high": np.quantile(dd, .975),
                                "interpretation": "descriptive; native language is confounded with nationality and cohort"})
    pd.DataFrame(cohort_rows).to_csv(OUT / "native_cohort_comparison.csv", index=False)

    # Paired participant-level contrasts; no window-level tests. Primary endpoint is recall.
    per_lookup = {key: g.set_index("subject").sort_index()
                  for key, g in corrected.groupby(keys)}
    full_lookup = {key: g.set_index("subject").sort_index()
                   for key, g in legacy.groupby(keys)}
    comparisons = []
    for direction in ["Arabic->Hindi", "Hindi->Arabic"]:
        candidates = [
            ("enrollment_ICA_minus_full_session_ICA", (direction, "ica_enrollment_only", "power", "logreg"), "legacy"),
            ("enrollment_ICA_minus_filtered_no_ICA", (direction, "ica_enrollment_only", "power", "logreg"), (direction, "filtered_no_ica", "power", "logreg")),
            ("SVM_minus_logistic", (direction, "ica_enrollment_only", "power", "linear_svm"), (direction, "ica_enrollment_only", "power", "logreg")),
            ("shrinkage_LDA_minus_logistic", (direction, "ica_enrollment_only", "power", "shrinkage_lda"), (direction, "ica_enrollment_only", "power", "logreg")),
            ("coherence_minus_power", (direction, "ica_enrollment_only", "coherence", "logreg"), (direction, "ica_enrollment_only", "power", "logreg")),
            ("fused_minus_power", (direction, "ica_enrollment_only", "power_plus_coherence", "logreg"), (direction, "ica_enrollment_only", "power", "logreg")),
        ]
        for label, akey, bkey in candidates:
            a = per_lookup[akey]
            b = full_lookup[(direction, "legacy_full_session_ica", "power", "logreg")] if bkey == "legacy" else per_lookup[bkey]
            x = a.recall.to_numpy(); y = b.recall.to_numpy(); d = x-y
            mean, lo, hi = boot_ci(d)
            test = wilcoxon(x, y, alternative="two-sided", method="auto")
            comparisons.append({"direction": direction, "contrast": label, "n_participants": len(d),
                                "mean_recall_difference": mean, "paired_bootstrap_ci95_low": lo,
                                "paired_bootstrap_ci95_high": hi, "wilcoxon_p_raw": test.pvalue})
    comp = pd.DataFrame(comparisons)
    comp["wilcoxon_p_holm"] = holm(comp.wilcoxon_p_raw.to_numpy())
    comp.to_csv(OUT / "paired_participant_comparisons.csv", index=False)

    # Row-normalized primary confusion matrices for each direction.
    for direction in ["Arabic->Hindi", "Hindi->Arabic"]:
        tr, te = direction.split("->")
        path = OUT / f"confusion_ica_enrollment_only_power_{tr}_to_{te}.csv"
        cm = pd.read_csv(path, index_col=0).to_numpy(float)
        cmn = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
        np.savetxt(OUT / f"confusion_ica_enrollment_only_power_normalized_{tr}_to_{te}.csv",
                   cmn, delimiter=",", fmt="%.6f")

    # A readable audit of demographic collinearity in the enrolled cohort.
    demographics = pd.DataFrame({"subject": SUBJECTS, "native_language": [NATIVE[s] for s in SUBJECTS],
                                 "nationality_cohort": ["Yemeni" if NATIVE[s] == "Arabic" else "Indian" for s in SUBJECTS],
                                 "sex_group": [SEX[s] for s in SUBJECTS]})
    demographics.to_csv(OUT / "demographic_cohort_map.csv", index=False)
    clustered_test_duration()
    confusion_figure()
    print("group and paired analyses complete")
    print(pd.read_csv(OUT / "native_cohort_comparison.csv").round(3).to_string(index=False))
    print(pd.read_csv(OUT / "paired_participant_comparisons.csv").round(4).to_string(index=False))


if __name__ == "__main__":
    main()
