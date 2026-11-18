"""EEGNet (Lawhern et al. 2018) + a train/eval loop. Model selection uses validation data from the
TRAINING language only; the test language is never seen until the final evaluation."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import balanced_accuracy_score

DEV = "cuda" if torch.cuda.is_available() else "cpu"


class EEGNet(nn.Module):
    def __init__(self, n_ch, n_cls, n_t, F1=8, D=2, k=64, drop=0.5):
        super().__init__()
        F2 = F1 * D
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


def val_split(tr, subj, order):
    """Validation = the last file of every subject's training block (all 20 classes present)."""
    va = np.zeros_like(tr)
    for s in np.unique(subj[tr]):
        m = tr & (subj == s)
        va |= m & (order == order[m].max())
    return tr & ~va, va


def train_eval(X, y, fit, va, te, seed, F1=8, D=2, k=64, drop=0.5, lr=1e-3, wd=0.0,
               epochs=300, patience=40, batch=64, shift=0):
    """shift>0: random circular time-shift augmentation of up to `shift` samples."""
    torch.manual_seed(seed); np.random.seed(seed)
    mu, sd = X[fit].mean((0, 2), keepdims=True), X[fit].std((0, 2), keepdims=True) + 1e-6
    T = lambda m: torch.tensor((X[m] - mu) / sd).unsqueeze(1)
    Xf, yf, Xv, yv = T(fit), torch.tensor(y[fit]), T(va).to(DEV), y[va]
    model = EEGNet(X.shape[1], int(y.max()) + 1, X.shape[2], F1, D, k, drop).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    lossf = nn.CrossEntropyLoss()
    best, state, wait, ep = -1.0, None, 0, 0
    for ep in range(1, epochs + 1):
        model.train(); perm = torch.randperm(len(Xf))
        for i in range(0, len(perm), batch):
            b = perm[i:i + batch]; xb = Xf[b]
            if shift:
                xb = torch.roll(xb, int(np.random.randint(-shift, shift + 1)), dims=-1)
            opt.zero_grad(); lossf(model(xb.to(DEV)), yf[b].to(DEV)).backward(); opt.step()
        model.eval()
        with torch.no_grad():
            acc = balanced_accuracy_score(yv, model(Xv).argmax(1).cpu().numpy())
        if acc > best:
            best, state, wait = acc, {k_: v.clone() for k_, v in model.state_dict().items()}, 0
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(state); model.eval()
    test = None
    if te is not None:
        Xt = T(te).to(DEV)
        with torch.no_grad():
            pred = torch.cat([model(Xt[i:i + 256]).argmax(1).cpu() for i in range(0, len(Xt), 256)]).numpy()
        test = balanced_accuracy_score(y[te], pred)
    return dict(val_acc=best, test_acc=test, epochs=ep)
