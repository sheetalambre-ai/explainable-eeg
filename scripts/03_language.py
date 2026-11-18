"""Part C. Language decoding under three split schemes, plus controls.

Tasks
  stimulus   : Arabic vs Hindi stimulus block (the label used in prior work)
  time_ctrl  : early vs late half WITHIN each language block (same language, only time differs)
  familiarity: L1 vs L2 (stimulus language == participant's native language)

Every subject saw the Arabic block first and the Hindi block second, so `stimulus`
is confounded with time-on-task. `time_ctrl` measures how decodable pure time is.
`familiarity` flips the time direction between groups, so time alone cannot solve it.
Outputs: results/language.csv, results/language_per_subject.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from src.config import RESULTS, PIPELINES
from src.evaluate import load_features, cross_val, permutation_p, MODELS

N_PERM = 100


def labels(m: pd.DataFrame) -> dict:
    rank = m.groupby(["subject", "language"])["order"].rank(method="dense")
    size = m.groupby(["subject", "language"])["order"].transform("nunique")
    return {"stimulus": m.language.to_numpy(),
            "time_ctrl": np.where(rank <= size / 2, "early", "late"),
            "familiarity": m.familiarity.to_numpy()}


pipes = sys.argv[1:] or PIPELINES    # e.g. `python 03_language.py ica` (one per process saves RAM)
for pipe in pipes:
    rows, per_subj = [], []
    X, m, _ = load_features(pipe)
    files, subjects = m.file_id.to_numpy(), m.subject.to_numpy()
    for task, y in labels(m).items():
        for model in MODELS:
            for scheme, groups in [("window", files), ("file", files), ("subject", subjects)]:
                acc, folds, _ = cross_val(X, y, groups, scheme, model, return_folds=True)
                row = dict(pipeline=pipe, task=task, model=model, scheme=scheme, bal_acc=acc)
                if scheme == "subject":
                    if model == "logreg":
                        row["perm_p"], _ = permutation_p(X, y, groups, scheme, files, acc, N_PERM)
                    per_subj += [dict(pipeline=pipe, task=task, model=model, subject=s, bal_acc=f)
                                 for s, f in zip(np.unique(subjects), folds)]
                rows.append(row)
                print(row, flush=True)
    pd.DataFrame(rows).to_csv(RESULTS / f"language_{pipe}.csv", index=False)
    pd.DataFrame(per_subj).to_csv(RESULTS / f"language_per_subject_{pipe}.csv", index=False)
