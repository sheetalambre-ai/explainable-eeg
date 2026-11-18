"""Part D. Familiarity effect via difference-in-differences on band power.

Per subject: delta = mean(Hindi block) - mean(Arabic block) for each feature.
  Yemeni (L1 Arabic) : delta = L2 - L1 + drift
  Indian (L1 Hindi)  : delta = L1 - L2 + drift
If drift is equal across groups: (delta_Y - delta_I) / 2 = L2 - L1 familiarity effect.
Parallel-trend check: late-minus-early drift WITHIN the Arabic block, compared by group.
Outputs: results/did.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon
from statsmodels.stats.multitest import multipletests
from src.config import RESULTS, PIPELINES
from src.evaluate import load_features


def test(a, b):
    return mannwhitneyu(a, b).pvalue


rows = []
for pipe in PIPELINES:
    X, m, cols = load_features(pipe)
    df = pd.DataFrame(X, columns=cols).assign(subject=m.subject, language=m.language,
                                              native=m.native, order=m.order)
    blk = df.groupby(["subject", "language"])[cols].mean()
    delta = blk.xs("Hindi", level="language") - blk.xs("Arabic", level="language")
    native = df.groupby("subject").native.first()
    yem, ind = delta[native == "Arabic"], delta[native == "Hindi"]

    ar = df[df.language == "Arabic"]
    mid = ar.groupby("subject").order.transform("median")
    drift = ar[ar.order > mid].groupby("subject")[cols].mean() - ar[ar.order <= mid].groupby("subject")[cols].mean()

    for c in cols:
        rows.append(dict(
            pipeline=pipe, feature=c,
            time_effect=delta[c].mean(), p_time=wilcoxon(delta[c]).pvalue,
            familiarity_L2_minus_L1=(yem[c].mean() - ind[c].mean()) / 2, p_familiarity=test(yem[c], ind[c]),
            drift_diff_Y_minus_I=drift[c][native == "Arabic"].mean() - drift[c][native == "Hindi"].mean(),
            p_parallel_trend=test(drift[c][native == "Arabic"], drift[c][native == "Hindi"])))

out = pd.DataFrame(rows)
for p in ["p_time", "p_familiarity", "p_parallel_trend"]:
    out[p.replace("p_", "q_")] = out.groupby("pipeline")[p].transform(lambda s: multipletests(s, method="fdr_bh")[1])
out.to_csv(RESULTS / "did.csv", index=False)
print(out.groupby("pipeline")[["q_time", "q_familiarity", "q_parallel_trend"]]
      .agg(lambda s: int((s < 0.05).sum())).rename(columns=lambda c: f"n_sig_{c}"))
