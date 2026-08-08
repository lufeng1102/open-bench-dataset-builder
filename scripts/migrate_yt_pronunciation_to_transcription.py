#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CUSTOM_BLOCK_RE = re.compile(
    r'(?P<indent>[ \t]*)"custom": \{\n'
    r'(?P<inner>[ \t]*)"pronunciation": (?P<expr>.+?)(?:,)?\n'
    r'(?P=indent)\}(?P<trailing_comma>,)?\n',
    re.MULTILINE,
)

SIBLING_PRONUNCIATION_RE = re.compile(
    r'(?P<indent>[ \t]*)\},\n'
    r'(?P=indent)"pronunciation": (?P<expr>.+?),\n',
    re.MULTILINE,
)

MISSING_COMMA_BEFORE_PRONUNCIATION_RE = re.compile(
    r'(?P<line>[ \t]*"[^"\n]+": .+?)(?<!,)\n(?P<indent>[ \t]*)"pronunciation": ',
    re.MULTILINE,
)


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


def normalize_pronunciation_text(text: str) -> str:
    return " ".join(text.replace("-", " ").split())


def build_unsigned_text(text: str) -> str:
    normalized = normalize_pronunciation_text(text)
    unsigned = "".join(ch for ch in normalized if not ch.isdigit())
    return " ".join(unsigned.split())


def ensure_pronunciation_list(value: object) -> list[object]:
    if isinstance(value, str):
        return [normalize_pronunciation_text(value)]
    if isinstance(value, list):
        return [normalize_pronunciation_text(item) if isinstance(item, str) else item for item in value]
    return [value]


def ensure_unsigned_list(pronunciation_list: list[object]) -> list[object]:
    return [build_unsigned_text(item) if isinstance(item, str) else item for item in pronunciation_list]


def should_have_unsigned(transcription: dict) -> bool:
    return transcription.get("language") == "zh"


def migrate_sf_jsonl(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0

    changed_rows = 0
    annotations_changed = 0
    new_lines: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, 1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            row_changed = False
            for ann in item.get("annotation") or []:
                if not isinstance(ann, dict):
                    continue
                transcription = ann.get("transcription")
                custom = ann.get("custom")
                if not isinstance(transcription, dict) or not isinstance(custom, dict):
                    continue
                if "pronunciation" not in custom:
                    continue
                if "pronunciation" not in transcription:
                    transcription["pronunciation"] = custom["pronunciation"]
                pronunciation_list = ensure_pronunciation_list(transcription.get("pronunciation"))
                transcription["pronunciation"] = pronunciation_list
                if should_have_unsigned(transcription):
                    transcription["pronunciation_unsigned"] = ensure_unsigned_list(pronunciation_list)
                else:
                    transcription.pop("pronunciation_unsigned", None)
                transcription.pop("pronounciation_unsigned", None)
                del custom["pronunciation"]
                if not custom:
                    ann.pop("custom", None)
                row_changed = True
                annotations_changed += 1
            for ann in item.get("annotation") or []:
                if not isinstance(ann, dict):
                    continue
                transcription = ann.get("transcription")
                if not isinstance(transcription, dict):
                    continue
                pronunciation_value = transcription.get("pronunciation")
                if pronunciation_value is None:
                    continue
                normalized_values = ensure_pronunciation_list(pronunciation_value)
                if normalized_values != pronunciation_value:
                    transcription["pronunciation"] = normalized_values
                    row_changed = True
                if should_have_unsigned(transcription):
                    unsigned_values = ensure_unsigned_list(normalized_values)
                    if transcription.get("pronunciation_unsigned") != unsigned_values:
                        transcription["pronunciation_unsigned"] = unsigned_values
                        row_changed = True
                elif "pronunciation_unsigned" in transcription:
                    transcription.pop("pronunciation_unsigned", None)
                    row_changed = True
                if "pronounciation_unsigned" in transcription:
                    transcription.pop("pronounciation_unsigned", None)
                    row_changed = True
            if row_changed:
                changed_rows += 1
            new_lines.append(json.dumps(item, ensure_ascii=False))

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return changed_rows, annotations_changed


def migrate_make_script(path: Path) -> tuple[bool, int]:
    if not path.exists():
        return False, 0

    original = path.read_text(encoding="utf-8")

    def repl(match: re.Match[str]) -> str:
        inner = match.group("inner")
        expr = match.group("expr")
        transcription_indent = inner[: max(len(inner) - 4, 0)]
        return f'{transcription_indent}"pronunciation": {expr},\n'

    updated, count_custom = CUSTOM_BLOCK_RE.subn(repl, original)

    def fix_sibling(match: re.Match[str]) -> str:
        indent = match.group("indent")
        expr = match.group("expr")
        return f'{indent}    "pronunciation": {expr},\n{indent}}},\n'

    updated, count_sibling = SIBLING_PRONUNCIATION_RE.subn(fix_sibling, updated)
    updated, count_missing_comma = MISSING_COMMA_BEFORE_PRONUNCIATION_RE.subn(
        lambda match: f'{match.group("line")},\n{match.group("indent")}"pronunciation": ',
        updated,
    )
    line_changes = 0
    lines = updated.splitlines()
    normalized_lines: list[str] = []
    in_transcription = False
    transcription_depth = 0
    i = 0
    current_language: str | None = None
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not in_transcription and '"transcription": {' in line:
            in_transcription = True
            transcription_depth = line.count("{") - line.count("}")
            current_language = None
            normalized_lines.append(line)
            i += 1
            continue
        if in_transcription and '"language":' in stripped:
            if '"zh"' in stripped:
                current_language = "zh"
            else:
                current_language = "other"
        if in_transcription and '"pronunciation":' in stripped and '"pronunciation_unsigned":' not in stripped:
            prefix, suffix = line.split('"pronunciation":', 1)
            expr = suffix.strip()
            trailing_comma = expr.endswith(",")
            expr = expr[:-1].rstrip() if trailing_comma else expr
            if not expr.startswith("["):
                if "normalize_pronunciation(" in expr or '.replace("-", " ")' in expr or ".replace('-', ' ')" in expr:
                    expr = f"[{expr}]"
                else:
                    expr = f'[{expr}.replace("-", " ")]'
            base_expr = expr[1:-1].strip() if expr.startswith("[") and expr.endswith("]") else expr
            unsigned_expr = f'[" ".join("".join(ch for ch in {base_expr} if not ch.isdigit()).split())]'
            line = f'{prefix}"pronunciation": {expr},'
            normalized_lines.append(line)
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if '"pronounciation_unsigned":' in next_line:
                i += 1
            if current_language == "zh" and '"pronunciation_unsigned":' not in next_line:
                normalized_lines.append(f'{prefix}"pronunciation_unsigned": {unsigned_expr},')
                line_changes += 1
            i += 1
            if in_transcription:
                transcription_depth += line.count("{") - line.count("}")
                if transcription_depth <= 0:
                    in_transcription = False
                    transcription_depth = 0
                    current_language = None
            continue
        if in_transcription and '"pronunciation_unsigned":' in stripped and current_language != "zh":
            line_changes += 1
            i += 1
            continue
        normalized_lines.append(line)
        if in_transcription:
            transcription_depth += line.count("{") - line.count("}")
            if transcription_depth <= 0:
                in_transcription = False
                transcription_depth = 0
                current_language = None
        i += 1
    updated = "\n".join(normalized_lines)
    if original.endswith("\n"):
        updated += "\n"
    total = count_custom + count_sibling + count_missing_comma + line_changes
    if total == 0:
        return False, 0
    path.write_text(updated, encoding="utf-8")
    return True, total


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate uploaded YT datasets from custom.pronunciation to transcription.pronunciation."
    )
    parser.add_argument(
        "--datasets-root",
        type=Path,
        default=Path.cwd() / "datasets",
        help="Datasets root directory. Defaults to ./datasets",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional dataset names to restrict migration.",
    )
    args = parser.parse_args()

    datasets_root = args.datasets_root.resolve()
    only = set(args.only or [])

    for dataset_dir in iter_target_dirs(datasets_root):
        if only and dataset_dir.name not in only:
            continue
        sf_changed_rows, ann_changed = migrate_sf_jsonl(dataset_dir / "sf.jsonl")
        script_changed, script_rewrites = migrate_make_script(dataset_dir / "make_sf_jsonl.py")
        if sf_changed_rows or script_changed:
            print(
                f"{dataset_dir.name}\tsf_rows_changed={sf_changed_rows}\t"
                f"annotations_changed={ann_changed}\tscript_changed={int(script_changed)}\t"
                f"script_rewrites={script_rewrites}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
