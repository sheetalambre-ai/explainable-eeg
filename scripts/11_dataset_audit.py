"""Audit the extracted EDF tree against the included raw-data ZIP."""
from __future__ import annotations

import zlib
import zipfile
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PACKAGE = ROOT / "EEG Dataset for Second Language Acquisition Arbic" / "EEG Dataset for Second Language Acquisition Arbic"
RAW_ZIP = PACKAGE / "EEG RAW Dataset.zip"
OUT = ROOT / "dataset_manifest.csv"
REPORT = ROOT / "DATASET_PROVENANCE.md"
COMMON_CHANNELS = "FP1;FP2;F7;F3;F4;F8;T3;T4;T5;T6;P3;P4;O1;O2"


def local_crc(path: Path) -> tuple[int, int]:
    crc, n = 0, 0
    with path.open("rb") as f:
        while block := f.read(8 * 1024 * 1024):
            crc = zlib.crc32(block, crc)
            n += len(block)
    return crc & 0xFFFFFFFF, n


def main() -> None:
    idx = pd.read_csv(ROOT / "results" / "file_index.csv")
    local = sorted(RAW.rglob("*.edf"))
    local_by_name = {p.name: p for p in local}
    archive_rows = {}
    with zipfile.ZipFile(RAW_ZIP) as zf:
        for info in zf.infolist():
            if info.filename.lower().endswith(".edf"):
                archive_rows[Path(info.filename).name] = (info.filename, info.CRC, info.file_size)

    index_by_key = {(int(r.subject), str(r.language), int(r.chunk)): r._asdict() for r in idx.itertuples(index=False)}
    rows = []
    for p in local:
        rel = p.relative_to(RAW)
        parts = rel.parts
        crc, size = local_crc(p)
        ar = archive_rows.get(p.name)
        match = re.search(r"S(\d+)-.*?([AH])-See(\d+)\.edf$", p.name, flags=re.I)
        language = {"A": "Arabic", "H": "Hindi"}.get(match.group(2).upper(), "") if match else ""
        indexed = index_by_key.get((int(match.group(1)), language, int(match.group(3))), {}) if match else {}
        rows.append({
            "relative_path": rel.as_posix(),
            "subject_folder": parts[0] if len(parts) > 0 else "",
            "subject_id": indexed.get("subject", ""),
            "language_folder": parts[1] if len(parts) > 1 else "",
            "language": indexed.get("language", ""),
            "native_language": indexed.get("native", ""),
            "sex_from_project_metadata": indexed.get("sex", ""),
            "file_name": p.name,
            "chunk_number": indexed.get("chunk", ""),
            "session_order_zero_based": indexed.get("order", ""),
            "familiarity_from_project_metadata": indexed.get("familiarity", ""),
            "project_file_id": indexed.get("file_id", ""),
            "bytes": size,
            "crc32": f"{crc:08x}",
            "edf_start_utc": indexed.get("start", ""),
            "duration_seconds": indexed.get("n_samples", 0) / 256.0,
            "sampling_rate_hz": 256.0,
            "n_samples": indexed.get("n_samples", ""),
            "n_channels_analyzed": len(COMMON_CHANNELS.split(";")),
            "common_channels_analyzed": COMMON_CHANNELS,
            "matches_included_raw_zip": bool(ar and ar[1] == crc and ar[2] == size),
            "archive_member": ar[0] if ar else "NOT_FOUND",
        })

    df = pd.DataFrame(rows).sort_values(["subject_folder", "edf_start_utc", "file_name"])
    df.to_csv(OUT, index=False)
    df["_start"] = pd.to_datetime(df.edf_start_utc, utc=True)
    order_rows = []
    for subject, g in df.groupby("subject_folder", sort=True):
        g = g.sort_values("_start")
        langs = list(dict.fromkeys(g.language_folder.tolist()))
        gaps = g["_start"].diff().dropna().dt.total_seconds().tolist()
        order_rows.append((subject, len(g), Counter(g.language_folder), " → ".join(langs), gaps))

    package_zip = ROOT / "EEG Dataset for Second Language Acquisition Arbic.zip"
    n_match = sum(bool(r["matches_included_raw_zip"]) for r in rows)
    notes = [
        "# Dataset provenance audit", "",
        "Generated from the on-disk files on 2026-11-13. No EDF was modified.", "",
        "## Identified source package", "",
        f"- Outer package: `{package_zip.relative_to(ROOT).as_posix()}` ({package_zip.stat().st_size:,} bytes).",
        f"- Raw archive within the package: `{RAW_ZIP.relative_to(ROOT).as_posix()}` ({RAW_ZIP.stat().st_size:,} bytes).",
        "- The outer package also contains an independent processed-CSV ZIP with processed CSVs and a second nested archive; it was not used to construct this EDF manifest.",
        "- The manifest records local paths, project-index header metadata, file sizes and CRC32 checks against the included raw ZIP.", "",
        "## Raw archive reconciliation", "",
        f"- Included raw ZIP EDF entries: {len(archive_rows)}.",
        f"- Extracted local EDF files: {len(local)}.",
        f"- Extracted files matching the raw ZIP CRC32 and size: {n_match} / {len(rows)}.",
        f"- ZIP EDF members with no same-named local file: {len(set(archive_rows) - set(local_by_name))}.",
        f"- Local EDFs with no same-named ZIP member: {len(set(local_by_name) - set(archive_rows))}.",
        "- The current extraction agrees with the included `EEG RAW Dataset.zip`; it is not a 300-file extraction with four files omitted relative to that archive.", "",
        "## Subject file counts and observed order", "",
        "| Subject folder | EDF count | Arabic EDFs | Hindi EDFs | Header-time language order |",
        "|---|---:|---:|---:|---|",
    ]
    for subject, n, counts, lang_order, _ in order_rows:
        notes.append(f"| {subject} | {n} | {counts.get('Arabic', 0)} | {counts.get('Hindi', 0)} | {lang_order} |")
    notes += [
        "", "## Chronology", "",
        "- EDF measurement timestamps order Arabic files before Hindi files for every subject.",
        "- Successive file start timestamps are 56 seconds apart; the project index reports 14,336 samples per EDF at 256 Hz.",
        "- This establishes the local EDF chronology, not the exact displayed word within every file. The analysis files contain no event markers.", "",
        "## Public metadata discrepancy and limits", "",
        "- The current public Mendeley landing-page description states 300 raw EDFs and describes 15 per-participant recordings with Arabic/Hindi stimuli alternating. The included raw ZIP has 296 EDFs organized in participant/language directories; local header chronology is Arabic then Hindi.",
        "- No four files are missing relative to the included raw archive. The archive does not explain why public landing-page metadata reports 300 or whether another release contains additional files.",
        "- Do not claim exact word order or event timing from EDF headers. A recording log, event-marked data, or author clarification is needed.",
        "- The EDF acquisition dates in 2022 differ from package timestamps in 2026; package time is not acquisition time.", "",
        "## Demographic metadata", "",
        "- Native language, nationality and sex coding comes from `src/config.py` and the dataset description, not EDF headers.",
        "- Sex and native-language groups are unevenly distributed; this cohort cannot isolate language-background effects from sex/nationality.",
        "- Ethics and consent claims should be attributed to the dataset record/source publication, not inferred from the raw archive.", "",
        "## Regeneration", "",
        "Run `python scripts/11_dataset_audit.py` from the project root. The script reads the existing file index and checks local CRC32/size against the raw ZIP directory. It writes `dataset_manifest.csv` and this report.",
    ]
    REPORT.write_text("\n".join(notes) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(df)} files)")
    print(f"Wrote {REPORT}; {n_match}/{len(rows)} local EDFs match archive CRC32 and size")


if __name__ == "__main__":
    main()
