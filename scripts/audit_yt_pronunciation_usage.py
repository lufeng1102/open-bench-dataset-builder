#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def iter_target_dirs(datasets_root: Path) -> list[Path]:
    targets: list[Path] = []
    for path in sorted(datasets_root.iterdir()):
        if not path.is_dir():
            continue
        if "YT_" not in path.name:
            continue
        if not any(child.is_dir() and child.name.startswith("_phy_") for child in path.iterdir()):
            continue
        targets.append(path)
    return targets


def scan_sf_jsonl(sf_path: Path) -> dict[str, int | str]:
    if not sf_path.exists():
        return {
            "sf_status": "missing",
            "rows": 0,
            "custom_pronunciation_rows": 0,
            "transcription_pronunciation_rows": 0,
            "both_rows": 0,
        }

    rows = 0
    custom_rows = 0
    transcription_rows = 0
    both_rows = 0

    with sf_path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            rows += 1
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{sf_path}: line {line_no} invalid JSON: {exc}") from exc

            for ann in item.get("annotation") or []:
                if not isinstance(ann, dict):
                    continue
                transcription = ann.get("transcription") or {}
                custom = ann.get("custom") or {}
                has_custom = isinstance(custom, dict) and "pronunciation" in custom
                has_transcription = isinstance(transcription, dict) and "pronunciation" in transcription
                if has_custom:
                    custom_rows += 1
                if has_transcription:
                    transcription_rows += 1
                if has_custom and has_transcription:
                    both_rows += 1

    if custom_rows and transcription_rows:
        sf_status = "mixed"
    elif custom_rows:
        sf_status = "custom_only"
    elif transcription_rows:
        sf_status = "transcription_only"
    else:
        sf_status = "no_pronunciation"

    return {
        "sf_status": sf_status,
        "rows": rows,
        "custom_pronunciation_rows": custom_rows,
        "transcription_pronunciation_rows": transcription_rows,
        "both_rows": both_rows,
    }


def scan_script(script_path: Path) -> dict[str, str]:
    if not script_path.exists():
        return {"script_status": "missing"}

    text = script_path.read_text(encoding="utf-8")
    has_custom = '"custom": {' in text and '"pronunciation":' in text
    has_transcription = '"transcription": {' in text and '"pronunciation":' in text

    if has_custom and has_transcription:
        status = "mixed"
    elif has_custom:
        status = "custom_writer"
    elif has_transcription:
        status = "transcription_writer"
    else:
        status = "no_pronunciation_writer"

    return {"script_status": status}


def classify_issue(sf_status: str, script_status: str) -> str:
    if sf_status in {"custom_only", "mixed"} or script_status in {"custom_writer", "mixed"}:
        return "needs_fix"
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit uploaded YT datasets for pronunciation field placement."
    )
    parser.add_argument(
        "--datasets-root",
        type=Path,
        default=Path.cwd() / "datasets",
        help="Datasets root directory. Defaults to ./datasets",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the TSV report.",
    )
    args = parser.parse_args()

    datasets_root = args.datasets_root.resolve()
    if not datasets_root.exists():
        print(f"ERROR: datasets root not found: {datasets_root}")
        return 2

    rows: list[dict[str, str | int]] = []
    for dataset_dir in iter_target_dirs(datasets_root):
        sf_info = scan_sf_jsonl(dataset_dir / "sf.jsonl")
        script_info = scan_script(dataset_dir / "make_sf_jsonl.py")
        issue = classify_issue(str(sf_info["sf_status"]), str(script_info["script_status"]))
        rows.append(
            {
                "issue": issue,
                "dataset_dir": str(dataset_dir),
                "dataset_name": dataset_dir.name,
                "sf_status": sf_info["sf_status"],
                "rows": sf_info["rows"],
                "custom_pronunciation_rows": sf_info["custom_pronunciation_rows"],
                "transcription_pronunciation_rows": sf_info["transcription_pronunciation_rows"],
                "both_rows": sf_info["both_rows"],
                "script_status": script_info["script_status"],
            }
        )

    header = [
        "issue",
        "dataset_name",
        "sf_status",
        "rows",
        "custom_pronunciation_rows",
        "transcription_pronunciation_rows",
        "both_rows",
        "script_status",
        "dataset_dir",
    ]
    lines = ["\t".join(header)]
    for row in rows:
        lines.append("\t".join(str(row[key]) for key in header))

    report = "\n".join(lines) + "\n"
    if args.output is not None:
        output_path = args.output.resolve()
        output_path.write_text(report, encoding="utf-8")
        print(output_path)
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
