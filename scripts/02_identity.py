"""Part B. Who is this? 20-way subject identification, within and across stimulus language.
Output: results/identity.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from sklearn.metrics import balanced_accuracy_score
from src.config import RESULTS, PIPELINES
from src.evaluate import load_features, cross_val, MODELS

rows = []
for pipe in PIPELINES:
    X, m, _ = load_features(pipe)
    y = m.subject.to_numpy()
    for model in MODELS:
        for scheme in ["window", "file"]:   # file: test windows come from unseen files
            acc = cross_val(X, y, m.file_id.to_numpy(), scheme, model)
            rows.append(dict(pipeline=pipe, model=model, test="pooled", scheme=scheme, bal_acc=acc))
        for tr_lang, te_lang in [("Arabic", "Hindi"), ("Hindi", "Arabic")]:
            tr, te = (m.language == tr_lang).to_numpy(), (m.language == te_lang).to_numpy()
            clf = MODELS[model]().fit(X[tr], y[tr])
            acc = balanced_accuracy_score(y[te], clf.predict(X[te]))
            rows.append(dict(pipeline=pipe, model=model, test=f"train {tr_lang} -> test {te_lang}",
                             scheme="cross-language", bal_acc=acc))
        print(pipe, model, "done")

out = pd.DataFrame(rows).assign(chance=1 / 20)
out.to_csv(RESULTS / "identity.csv", index=False)
print(out.to_string(index=False))
