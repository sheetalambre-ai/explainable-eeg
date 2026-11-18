"""Part A. Index files, preprocess each subject with every pipeline, save window features.
Outputs: results/file_index.csv, results/features_<pipeline>.csv, results/quality.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from src.config import RESULTS, PIPELINES, CHANNELS
from src.data import index_files, load_subject
from src.features import preprocess, window_features

RESULTS.mkdir(parents=True, exist_ok=True)
files = index_files()
files.drop(columns="path").to_csv(RESULTS / "file_index.csv", index=False)
print(f"{len(files)} files, {files.subject.nunique()} subjects")

quality_rows = []
for pipe in PIPELINES:
    parts = []
    for subj, sf in files.groupby("subject"):
        raw = preprocess(load_subject(sf), pipe)
        data, start = raw.get_data(), 0
        n_ica = raw.info.get("description") or ""
        # split the concatenated signal back into its files
        for _, row in sf.iterrows():
            length = int(row.n_samples)
            X, names, q = window_features(data[:, start:start + length], CHANNELS)
            start += length
            meta = row.drop(["path", "start", "n_samples"]).to_dict()
            df = pd.DataFrame(X, columns=names).assign(**meta, window=range(len(X)))
            parts.append(df)
            quality_rows += [dict(pipeline=pipe, subject=subj, file_id=row.file_id,
                                  ptp_uv=a, line_ratio=b, ica_info=n_ica) for a, b in q]
        print(pipe, subj, "done")
    pd.concat(parts).to_csv(RESULTS / f"features_{pipe}.csv", index=False)
pd.DataFrame(quality_rows).to_csv(RESULTS / "quality.csv", index=False)
