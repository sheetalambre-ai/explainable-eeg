"""EEGNet-8,2 (Lawhern et al. 2018) baseline under the cross-language protocol.
Input: ICA-cleaned 4-s windows downsampled to 128 Hz (data are already low-passed at 45 Hz).
Training: one language block; 10% of its FILES held out for early stopping. Test: other block.
Output: results/eegnet.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import balanced_accuracy_score
from src.config import RESULTS, SEED

EPOCHS, PATIENCE, BATCH, LR = 300, 30, 64, 1e-3
DEV = "cuda" if torch.cuda.is_available() else "cpu"


class EEGNet(nn.Module):
    def __init__(self, n_ch, n_cls, n_t, F1=8, D=2, F2=16, k=64, drop=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, F1, (1, k), padding=(0, k // 2), bias=False), nn.BatchNorm2d(F1),
            nn.Conv2d(F1, F1 * D, (n_ch, 1), groups=F1, bias=False), nn.BatchNorm2d(F1 * D), nn.ELU(),
            nn.AvgPool2d((1, 4)), nn.Dropout(drop),
            nn.Conv2d(F1 * D, F1 * D, (1, 16), padding=(0, 8), groups=F1 * D, bias=False),
            nn.Conv2d(F1 * D, F2, 1, bias=False), nn.BatchNorm2d(F2), nn.ELU(),
            nn.AvgPool2d((1, 8)), nn.Dropout(drop), nn.Flatten())
        with torch.no_grad():
            n_flat = self.net(torch.zeros(1, 1, n_ch, n_t)).shape[1]
        self.fc = nn.Linear(n_flat, n_cls)

    def forward(self, x):
        return self.fc(self.net(x))


def run(X, y, tr, te, files, seed):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    tr_files = np.unique(files[tr]); val_files = rng.choice(tr_files, max(1, len(tr_files) // 10), replace=False)
    va = tr & np.isin(files, val_files); fit = tr & ~va
    mu, sd = X[fit].mean((0, 2), keepdims=True), X[fit].std((0, 2), keepdims=True) + 1e-6
    T = lambda m: torch.tensor((X[m] - mu) / sd).unsqueeze(1)
    Xf, yf, Xv, yv, Xt = T(fit), torch.tensor(y[fit]), T(va).to(DEV), y[va], T(te).to(DEV)
    model = EEGNet(X.shape[1], int(y.max()) + 1, X.shape[2]).to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=LR); lossf = nn.CrossEntropyLoss()
    best, best_state, wait = -1, None, 0
    for ep in range(EPOCHS):
        model.train(); perm = torch.randperm(len(Xf))
        for i in range(0, len(perm), BATCH):
            b = perm[i:i + BATCH]
            opt.zero_grad(); lossf(model(Xf[b].to(DEV)), yf[b].to(DEV)).backward(); opt.step()
        model.eval()
        with torch.no_grad():
            acc = balanced_accuracy_score(yv, model(Xv).argmax(1).cpu().numpy())
        if acc > best:
            best, best_state, wait = acc, {k: v.clone() for k, v in model.state_dict().items()}, 0
        else:
            wait += 1
            if wait >= PATIENCE:
                break
    model.load_state_dict(best_state); model.eval()
    with torch.no_grad():
        pred = torch.cat([model(Xt[i:i + 256]).argmax(1).cpu() for i in range(0, len(Xt), 256)]).numpy()
    return balanced_accuracy_score(y[te], pred), best, ep + 1


d = np.load(RESULTS / "windows_ica.npz")
X = d["X"][:, :, ::2].copy()                      # 256 -> 128 Hz
subj, lang, files = d["subject"], d["language"], d["file_id"]
y = np.searchsorted(np.unique(subj), subj)
rows = []
for a, b in [("Arabic", "Hindi"), ("Hindi", "Arabic")]:
    for seed in [SEED, SEED + 1, SEED + 2]:
        acc, val, ep = run(X, y, lang == a, lang == b, files, seed)
        rows.append(dict(direction=f"{a}->{b}", seed=seed, bal_acc=acc, val_acc=val, epochs=ep))
        print(rows[-1], flush=True)
df = pd.DataFrame(rows); df.to_csv(RESULTS / "eegnet.csv", index=False)
print(df.groupby("direction").bal_acc.agg(["mean", "std"]).round(3))
