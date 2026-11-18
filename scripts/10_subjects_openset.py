"""(a) Per-subject accuracy, confusion matrix and subject-bootstrap 95% CIs (cross-language).
(b) Open-set test: 4 subjects per fold are never enrolled; can the system reject them?
ICA band power + logistic regression throughout.
Outputs: results/bio_subjects.csv, results/bio_ci.csv, results/bio_openset.csv,
         results/figures/fig5_confusion.png"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import recall_score, roc_auc_score, confusion_matrix
from src.config import RESULTS, FIGURES, SEED
from src.evaluate import load_features, MODELS

X, m, cols = load_features("ica")
y, lang, files = m.subject.to_numpy(), m.language.to_numpy(), m.file_id.to_numpy()
subjects = np.unique(y)
DIRS = [("Arabic", "Hindi"), ("Hindi", "Arabic")]
rng = np.random.default_rng(SEED)
cols = np.array(cols)
band = np.array([c.split("_")[1] for c in cols]); ch = np.array([c.split("_")[0] for c in cols])
emg_safe = np.isin(band, ["delta", "theta", "alpha"]) & np.isin(ch, ["F3", "F4", "P3", "P4", "O1", "O2"])


def boot_ci(per_subj, n=2000):
    v = np.array(per_subj); bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


# ---- (a) per-subject + CI ----
subj_rows, ci_rows, cm_total = [], [], np.zeros((len(subjects), len(subjects)))
for fname, sel in [("all features", slice(None)), ("1-13 Hz, EMG-safe sites", emg_safe)]:
    for a, b in DIRS:
        tr, te = lang == a, lang == b
        pred = MODELS["logreg"]().fit(X[tr][:, sel], y[tr]).predict(X[te][:, sel])
        rec = recall_score(y[te], pred, labels=subjects, average=None)
        if fname == "all features":
            cm_total += confusion_matrix(y[te], pred, labels=subjects)
            subj_rows += [dict(direction=f"{a}->{b}", subject=s, native=m.native[m.subject == s].iloc[0],
                               recall=r) for s, r in zip(subjects, rec)]
        mean, lo, hi = boot_ci(rec)
        ci_rows.append(dict(features=fname, direction=f"{a}->{b}", bal_acc=mean, ci_low=lo, ci_high=hi,
                            min_subject=rec.min(), n_below_80=int((rec < 0.8).sum())))
pd.DataFrame(subj_rows).to_csv(RESULTS / "bio_subjects.csv", index=False)
ci = pd.DataFrame(ci_rows); ci.to_csv(RESULTS / "bio_ci.csv", index=False)
print(ci.round(3).to_string(index=False))

cmn = cm_total / cm_total.sum(1, keepdims=True)
fig, ax = plt.subplots(figsize=(4.6, 4))
im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(20), subjects, fontsize=6); ax.set_yticks(range(20), subjects, fontsize=6)
ax.axhline(9.5, c="r", lw=.6); ax.axvline(9.5, c="r", lw=.6)
ax.set_xlabel("predicted subject"); ax.set_ylabel("true subject")
ax.set_title("Cross-language confusion (both directions)", fontsize=9)
fig.colorbar(im, fraction=.046); fig.tight_layout(); fig.savefig(FIGURES / "fig5_confusion.png", dpi=200)

# ---- (b) open-set ----
open_rows = []
order = rng.permutation(subjects)
for fold, unknown in enumerate(np.array_split(order, 5)):
    for a, b in DIRS:
        tr = (lang == a) & ~np.isin(y, unknown); te = lang == b
        clf = MODELS["logreg"]().fit(X[tr], y[tr])
        P = clf.predict_proba(X[te]); mt = m[te].reset_index(drop=True)
        for k in [1, 4]:                                   # 4 s and 16 s of evidence
            key = (mt.file_id + "_" + (mt.groupby("file_id").cumcount() // k).astype(str)).values
            Pk = pd.DataFrame(P).groupby(key).mean()
            yk = mt.groupby(key).subject.first().loc[Pk.index].to_numpy()
            score, guess = Pk.max(1).to_numpy(), clf.classes_[Pk.to_numpy().argmax(1)]
            is_unk = np.isin(yk, unknown)
            row = dict(fold=fold, direction=f"{a}->{b}", seconds=4 * k,
                       auroc_known_vs_unknown=roc_auc_score(~is_unk, score))
            for fpir in [0.01, 0.05, 0.10]:
                t = np.quantile(score[is_unk], 1 - fpir)
                row[f"DIR@FPIR{int(fpir*100)}%"] = float(np.mean((guess[~is_unk] == yk[~is_unk]) & (score[~is_unk] > t)))
            open_rows.append(row)
op = pd.DataFrame(open_rows); op.to_csv(RESULTS / "bio_openset.csv", index=False)
print(op.groupby("seconds").mean(numeric_only=True).drop(columns="fold").round(3))
