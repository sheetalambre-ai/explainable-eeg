"""Shared model + cross-validation helpers."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score
import pandas as pd
from .config import SEED, RESULTS

META = ["subject", "language", "chunk", "native", "sex", "order", "minutes",
        "familiarity", "file_id", "window"]


def load_features(pipeline: str):
    df = pd.read_csv(RESULTS / f"features_{pipeline}.csv")
    feat_cols = [c for c in df.columns if c not in META]
    return df[feat_cols].to_numpy(), df[META].reset_index(drop=True), feat_cols

MODELS = {
    "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000)),
    "rf": lambda: RandomForestClassifier(n_estimators=300, n_jobs=1, random_state=SEED),
}


def splitter(scheme: str, n_splits: int = 5):
    """window = leaky random split; file = windows of a file stay together;
    subject = leave-one-subject-out (groups must be subject ids)."""
    if scheme == "window":
        return KFold(n_splits, shuffle=True, random_state=SEED)
    if scheme in ("file", "subject"):
        return GroupKFold(n_splits)
    raise ValueError(scheme)


def cross_val(X, y, groups, scheme, model="logreg", n_splits=5, return_folds=False):
    """Balanced accuracy pooled over folds (+ optional per-fold scores)."""
    if scheme == "subject":
        n_splits = len(np.unique(groups))
    pred = np.empty_like(y)
    folds = []
    for tr, te in splitter(scheme, n_splits).split(X, y, groups):
        clf = MODELS[model]().fit(X[tr], y[tr])
        pred[te] = clf.predict(X[te])
        folds.append(balanced_accuracy_score(y[te], pred[te]) if len(np.unique(y[te])) > 1
                     else float(np.mean(pred[te] == y[te])))
    score = balanced_accuracy_score(y, pred)
    return (score, folds, pred) if return_folds else score


def permutation_p(X, y, groups, scheme, perm_groups, observed, n_perm=100, model="logreg"):
    """Shuffle labels at the level of perm_groups (whole files), recompute score."""
    rng = np.random.default_rng(SEED)
    uniq = np.unique(perm_groups)
    lab = {g: y[perm_groups == g][0] for g in uniq}
    null = []
    for _ in range(n_perm):
        shuffled = dict(zip(uniq, rng.permutation([lab[g] for g in uniq])))
        y_p = np.array([shuffled[g] for g in perm_groups])
        null.append(cross_val(X, y_p, groups, scheme, model))
    null = np.array(null)
    return float((1 + (null >= observed).sum()) / (1 + n_perm)), null
