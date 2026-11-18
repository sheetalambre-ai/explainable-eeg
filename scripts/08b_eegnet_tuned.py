"""Tuned EEGNet baseline (cross-language). Fair protocol:
  1) for each direction, grid-search on validation = last file of each subject in the TRAINING block;
  2) pick the config with best mean validation accuracy over both directions (one config for the paper);
  3) retrain with 3 seeds and evaluate once on the other language.
Test accuracy is never used for selection. Outputs: results/eegnet_tuning.csv, results/eegnet_tuned.csv"""
import sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from src.config import RESULTS, SEED
from src.eegnet import train_eval, val_split

d = np.load(RESULTS / "windows_ica.npz")
X = d["X"][:, :, ::2].copy()                                   # 128 Hz
subj, lang, order = d["subject"], d["language"], d["order"]
y = np.searchsorted(np.unique(subj), subj)
DIRS = [("Arabic", "Hindi"), ("Hindi", "Arabic")]

GRID = dict(F1=[8, 16], drop=[0.25, 0.5], lr=[1e-3, 3e-4], wd=[0.0, 1e-2], shift=[0, 32])
configs = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]

rows = []
for ci, cfg in enumerate(configs):
    for a, _ in DIRS:
        fit, va = val_split(lang == a, subj, order)
        r = train_eval(X, y, fit, va, None, SEED, **cfg)
        rows.append(dict(config=ci, train=a, **cfg, val_acc=r["val_acc"], epochs=r["epochs"]))
        print(rows[-1], flush=True)
tune = pd.DataFrame(rows); tune.to_csv(RESULTS / "eegnet_tuning.csv", index=False)

best_ci = tune.groupby("config").val_acc.mean().idxmax()
best = configs[best_ci]
print("selected config", best_ci, best, flush=True)

final = []
for a, b in DIRS:
    fit, va = val_split(lang == a, subj, order)
    for seed in [SEED, SEED + 1, SEED + 2]:
        r = train_eval(X, y, fit, va, lang == b, seed, **best)
        final.append(dict(direction=f"{a}->{b}", seed=seed, **best, **r))
        print(final[-1], flush=True)
f = pd.DataFrame(final); f.to_csv(RESULTS / "eegnet_tuned.csv", index=False)
print(f.groupby("direction").test_acc.agg(["mean", "std"]).round(3))
