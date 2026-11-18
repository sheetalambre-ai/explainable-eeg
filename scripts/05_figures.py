"""Paper figures + tables, generated only from results/*.csv.
Outputs: results/figures/*.png, results/tables.md"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.config import RESULTS, FIGURES, CHANNELS, BANDS

FIGURES.mkdir(parents=True, exist_ok=True)
q = pd.read_csv(RESULTS / "quality.csv")
ident = pd.read_csv(RESULTS / "identity.csv")
lang = pd.concat(pd.read_csv(p) for p in sorted(RESULTS.glob("language_[!p]*.csv")))
did = pd.read_csv(RESULTS / "did.csv")

# Fig 1: signal quality per pipeline
fig, ax = plt.subplots(1, 2, figsize=(8, 3))
for i, col in enumerate(["ptp_uv", "line_ratio"]):
    q.boxplot(column=col, by="pipeline", ax=ax[i], showfliers=False)
    ax[i].set_title(col); ax[i].set_xlabel("")
ax[0].set_yscale("log")
fig.suptitle("Signal quality by preprocessing pipeline"); fig.tight_layout()
fig.savefig(FIGURES / "fig1_quality.png", dpi=200)

# Fig 2: decoding accuracy by task x split scheme (logreg, ica)
sub = lang[(lang.model == "logreg") & (lang.pipeline == "ica")]
piv = sub.pivot(index="task", columns="scheme", values="bal_acc")[["window", "file", "subject"]]
ax = piv.plot.bar(figsize=(6, 3.5), rot=0)
ax.axhline(0.5, ls="--", c="k", lw=1); ax.set_ylabel("balanced accuracy"); ax.set_ylim(0, 1)
ax.set_title("Language decoding vs split scheme (ICA, logistic regression)")
plt.tight_layout(); plt.savefig(FIGURES / "fig2_language_splits.png", dpi=200)

# Fig 3: familiarity (DiD) effect, channel x band, relative power, ICA pipeline
d = did[(did.pipeline == "ica") & did.feature.str.endswith("_rel")].copy()
d[["ch", "band"]] = d.feature.str.split("_", expand=True)[[0, 1]]
mat = d.pivot(index="band", columns="ch", values="familiarity_L2_minus_L1").loc[list(BANDS), CHANNELS]
fig, ax = plt.subplots(figsize=(8, 3))
v = np.nanmax(np.abs(mat.values))
im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-v, vmax=v, aspect="auto")
ax.set_xticks(range(len(CHANNELS)), CHANNELS, rotation=90); ax.set_yticks(range(len(BANDS)), list(BANDS))
fig.colorbar(im, label="L2 - L1 relative power")
ax.set_title("Familiarity effect (difference-in-differences), ICA")
fig.tight_layout(); fig.savefig(FIGURES / "fig3_familiarity_did.png", dpi=200)

# Tables
with open(RESULTS / "tables.md", "w") as f:
    f.write("## Quality (median per pipeline)\n\n")
    f.write(q.groupby("pipeline")[["ptp_uv", "line_ratio"]].median().round(4).to_markdown() + "\n\n")
    f.write("## Identity decoding\n\n" + ident.round(3).to_markdown(index=False) + "\n\n")
    f.write("## Language decoding\n\n" + lang.round(3).to_markdown(index=False) + "\n\n")
    f.write("## DiD: features with q<0.05 (count)\n\n")
    f.write(did.groupby("pipeline")[["q_time", "q_familiarity", "q_parallel_trend"]]
            .agg(lambda s: int((s < 0.05).sum())).to_markdown() + "\n\n")
    f.write("## DiD: 10 smallest familiarity p-values (ICA)\n\n")
    f.write(did[did.pipeline == "ica"].nsmallest(10, "p_familiarity")
            [["feature", "familiarity_L2_minus_L1", "p_familiarity", "q_familiarity",
              "p_parallel_trend"]].round(4).to_markdown(index=False) + "\n")
print("figures + tables written")

# ---- Biometrics paper (needs scripts/06_biometrics.py outputs) ----
if (RESULTS / "bio_duration.csv").exists():
    dur = pd.read_csv(RESULTS / "bio_duration.csv")
    abl = pd.read_csv(RESULTS / "bio_ablation.csv")
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    for d, g in dur.groupby("direction"):
        ax[0].plot(g.seconds, g.bal_acc, marker="o", label=d)
    ax[0].set_xscale("log", base=2); ax[0].set_xticks([4, 8, 16, 32], ["4", "8", "16", "32"])
    ax[0].set_xlabel("test evidence (s)"); ax[0].set_ylabel("identification accuracy (20 subjects)")
    ax[0].axhline(1 / 20, ls="--", c="k", lw=1); ax[0].set_ylim(0, 1); ax[0].legend()
    ax[0].set_title("Cross-language identification")
    sub = abl[abl.kind.isin(["band", "region"])]
    ax[1].barh(sub.kind + ": " + sub.subset, sub.bal_acc, color=np.where(sub.kind == "band", "C0", "C1"))
    ax[1].axvline(abl.loc[abl.kind == "all", "bal_acc"].item(), ls=":", c="k", label="all features")
    ax[1].axvline(1 / 20, ls="--", c="k", lw=1); ax[1].set_xlim(0, 1); ax[1].legend(loc="upper right")
    ax[1].set_title("Feature ablation (4 s, cross-language)")
    fig.tight_layout(); fig.savefig(FIGURES / "fig4_biometrics.png", dpi=200)
    print("biometric figure written")
