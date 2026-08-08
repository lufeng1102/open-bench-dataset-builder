#!/usr/bin/env python3
"""Validate common mutual-exclusion rules for physical testset sf.jsonl."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def has_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def validate_annotation(annotation: dict[str, Any], line_no: int, ann_idx: int) -> list[str]:
    errors: list[str] = []
    transcription = annotation.get("transcription") or {}
    timestamp = annotation.get("timestamp")

    has_timestamp = isinstance(timestamp, dict) and (
        "begin_time" in timestamp or "end_time" in timestamp
    )
    has_keyword = has_value(transcription.get("keyword"))
    has_text = has_value(transcription.get("text"))
    has_repeat_times = has_value(transcription.get("repeat_times"))
    custom = annotation.get("custom") or {}

    prefix = f"line {line_no}, annotation[{ann_idx}]"

    if has_timestamp and has_keyword and has_repeat_times:
        errors.append(
            f"{prefix}: timestamp cannot coexist with transcription.keyword + transcription.repeat_times"
        )

    if has_keyword and has_text:
        errors.append(
            f"{prefix}: transcription.keyword cannot coexist with transcription.text"
        )

    pronunciation_values: list[str] = []
    for value in (
        transcription.get("pronunciation"),
        custom.get("pronunciation") if isinstance(custom, dict) else None,
    ):
        if isinstance(value, str):
            pronunciation_values.append(value)
        elif isinstance(value, list):
            pronunciation_values.extend(v for v in value if isinstance(v, str))

    for pronunciation in pronunciation_values:
        if "-" in pronunciation:
            errors.append(
                f"{prefix}: pronunciation must not contain '-' and should use spaces instead"
            )

    return errors


def validate_sf_jsonl(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue

            annotations = item.get("annotation") or []
            if not isinstance(annotations, list):
                errors.append(f"line {line_no}: annotation must be a list")
                continue

            for ann_idx, annotation in enumerate(annotations):
                if not isinstance(annotation, dict):
                    errors.append(f"line {line_no}, annotation[{ann_idx}]: must be an object")
                    continue
                errors.extend(validate_annotation(annotation, line_no, ann_idx))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate mutual-exclusion rules in physical testset sf.jsonl"
    )
    parser.add_argument(
        "sf_jsonl",
        nargs="?",
        default=Path.cwd() / "sf.jsonl",
        type=Path,
        help="Path to sf.jsonl. Defaults to ./sf.jsonl in the current working directory.",
    )
    args = parser.parse_args()

    sf_jsonl = args.sf_jsonl.resolve()
    if not sf_jsonl.exists():
        print(f"ERROR: file not found: {sf_jsonl}")
        return 2

    errors = validate_sf_jsonl(sf_jsonl)
    if errors:
        print(f"ERROR: validation failed for {sf_jsonl}")
        for err in errors[:200]:
            print(err)
        if len(errors) > 200:
            print(f"... truncated {len(errors) - 200} more errors")
        return 1

    print(f"OK: {sf_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
