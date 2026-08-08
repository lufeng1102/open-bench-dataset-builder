#!/usr/bin/env python3

import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


XLSX_PATH = Path("references/测试数据标签管理v20260325更新.xlsx")
OUT_DIR = Path("references/specs_20260325")

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

ROUTES = {
    "数据通用维度标签": "01_数据通用维度标签.md",
    "业务维度标签": "02_业务维度标签.md",
    "SP信号测试": "03_SP信号测试.md",
    "wakeup唤醒测试": "04_wakeup唤醒测试.md",
    "误唤醒测试": "05_误唤醒测试.md",
    "本地命令词自由说识别测试": "06_本地命令词自由说识别测试.md",
    "本地通用识别ngram测试": "07_本地通用识别ngram测试.md",
    "VP声纹测试": "08_VP声纹测试.md",
    "云端识别测试": "09_云端识别测试.md",
    "翻译测试": "10_翻译测试.md",
    "语义测试": "11_语义测试.md",
    "合成测试": "12_合成测试.md",
}

TASK_MAPPING = {
    "SP信号测试": "`SP`",
    "wakeup唤醒测试": "`WakeUp`",
    "误唤醒测试": "`FalseTrigger`",
    "本地命令词自由说识别测试": "`local_asr_cmd`",
    "本地通用识别ngram测试": "`local_asr_comm`",
    "VP声纹测试": "`VP`",
    "云端识别测试": "云端 `ASR`",
    "翻译测试": "`MT`",
    "语义测试": "`NLU`",
    "合成测试": "`TTS`",
}


class FieldRow:
    def __init__(self, label, key, level1, level2, level3, required, enum_text, note, row_no, section):
        self.label = label
        self.key = key
        self.level1 = level1
        self.level2 = level2
        self.level3 = level3
        self.required = required
        self.enum_text = enum_text
        self.note = note
        self.row_no = row_no
        self.section = section

    @property
    def path(self) -> str:
        if self.key:
            return self.key
        token1 = self._token(self.level1)
        token2 = self._token(self.level2)
        token3 = self._token(self.level3)
        for token in (token3, token2, token1):
            if "." in token:
                return token
        parts = [token1, token2, token3]
        return ".".join(part for part in parts if part)

    @staticmethod
    def _token(text: str) -> str:
        text = text.strip()
        if not text:
            return ""
        if "：" in text:
            return text.split("：")[-1].strip()
        if ":" in text:
            return text.split(":")[-1].strip()
        match = re.search(r"([A-Za-z][A-Za-z0-9_.-]*)$", text)
        if match:
            return match.group(1)
        return text


def col_idx(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch) - 64
    return value - 1


def read_shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in si.iter(f"{NS}t")) for si in root.findall(f"{NS}si")]


def read_sheet(zf, target, shared_strings):
    root = ET.fromstring(zf.read(target))
    rows = []
    for row in root.find(f"{NS}sheetData").findall(f"{NS}row"):
        values = [""] * 8
        for cell in row.findall(f"{NS}c"):
            idx = col_idx(cell.attrib["r"])
            if idx >= 8:
                continue
            kind = cell.attrib.get("t")
            value_node = cell.find(f"{NS}v")
            inline_node = cell.find(f"{NS}is")
            value = ""
            if kind == "s" and value_node is not None:
                value = shared_strings[int(value_node.text)]
            elif kind == "inlineStr" and inline_node is not None:
                value = "".join(node.text or "" for node in inline_node.iter(f"{NS}t"))
            elif value_node is not None and value_node.text is not None:
                value = value_node.text
            values[idx] = value.strip()
        rows.append(values)
    return rows


def parse_fields(rows):
    fields = []
    markers = []
    current_level1 = ""
    current_level2 = ""
    current_section = "通用维度字段"
    public_keys = set(["type", "source", "source_ds_id", "data_generate_time", "pms_id", "tag", "info"])
    for row_no, row in enumerate(rows, 1):
        label, key, level1, level2, level3, required, enum_text, note = row
        nonempty = [cell for cell in row if cell]
        if not nonempty:
            continue
        if row_no == 1:
            continue
        if len(nonempty) == 1 and not key and not level1 and not level2 and not level3:
            markers.append(label)
            if label == "本测试任务特有标签":
                current_section = "任务特有字段"
            continue
        if label == "数据通用维度标签":
            markers.append(label)
            current_section = "通用维度字段"
            continue
        if level1:
            current_level1 = level1
            current_level2 = ""
        if level2:
            current_level2 = level2
        effective_level1 = level1 or current_level1
        effective_level2 = level2 or current_level2
        section = current_section
        if key in public_keys:
            section = "数据集公共字段"
        fields.append(
            FieldRow(
                label=label,
                key=key,
                level1=effective_level1,
                level2=effective_level2,
                level3=level3,
                required=required,
                enum_text=enum_text,
                note=note,
                row_no=row_no,
                section=section,
            )
        )
    return fields, markers


def short_enum(text):
    text = text.strip()
    if not text:
        return ""
    text = " / ".join(part.strip() for part in text.split("|") if part.strip())
    if len(text) <= 80:
        return text
    parts = [part.strip() for part in text.split(" / ") if part.strip()]
    if len(parts) <= 6:
        return text
    return "{0} / ...".format(" / ".join(parts[:6]))


def section_key(field):
    return field.section


def field_table(fields):
    rows = [
        "| 字段路径 | 标签名称 | 必填 | 枚举/取值摘要 | 备注 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for field in fields:
        rows.append(
            "| {path} | {label} | {required} | {enum_text} | {note} |".format(
                path=field.path or "-",
                label=field.label or "-",
                required="Y" if field.required == "Y" else "",
                enum_text=short_enum(field.enum_text) or "-",
                note=field.note or "-",
            )
        )
    return "\n".join(rows)


def required_summary(fields):
    required = []
    seen = set()
    for field in fields:
        if field.required != "Y":
            continue
        if field.path in seen:
            continue
        seen.add(field.path)
        required.append(field.path)
    if not required:
        return "- 当前 sheet 没有额外标出必填字段。"
    return "- " + "\n- ".join(required)


def render_sheet(sheet_name, fields, markers):
    lines = [
        f"# {sheet_name} 结构化摘要",
        "",
        "- 来源：`references/测试数据标签管理v20260325更新.xlsx`",
        f"- 对应文件：`{ROUTES[sheet_name]}`",
    ]
    if sheet_name == "数据通用维度标签":
        lines.extend(
            [
                "- 适用范围：所有物理测试集的通用标签底座",
                "- 使用顺序：任何任务专属 sheet 之前先读这份；再结合 `02_业务维度标签.md` 和任务 sheet。",
            ]
        )
    elif sheet_name == "业务维度标签":
        lines.extend(
            [
                "- 适用范围：所有物理测试集的业务字段路由层",
                "- 使用顺序：在 `01_数据通用维度标签.md` 之后读取，用于确认 `project_name`、`application_domain`、`category`、`brand`、`environment`、`supported_tasks`。",
            ]
        )
    else:
        lines.extend(
            [
                f"- 适用任务：{TASK_MAPPING[sheet_name]}",
                "- 使用顺序：先读 `01_数据通用维度标签.md` 和 `02_业务维度标签.md`，再读当前任务 sheet。",
            ]
        )
    if markers:
        lines.append(f"- 表内分段标记：`{'`、`'.join(markers)}`")
    lines.extend(
        [
            "",
            "## 必填字段速览",
            required_summary(fields),
            "",
        ]
    )

    order = ["通用维度字段", "数据集公共字段", "任务特有字段"]
    for name in order:
        bucket = [field for field in fields if section_key(field) == name]
        if not bucket:
            continue
        lines.extend([f"## {name}", "", field_table(bucket), ""])

    if sheet_name not in ("数据通用维度标签", "业务维度标签"):
        task_fields = [field.path for field in fields if section_key(field) == "任务特有字段"]
        lines.extend(
            [
                "## 使用提示",
                "",
                f"- 当前 sheet 明确增量字段：{', '.join(task_fields) if task_fields else '未额外列出字段'}。",
                "- 若任务 sheet 里的通用字段与 `01`/`02` 重复，执行时仍应以三者组合判断，不要只看当前文件。",
                "- 物理训练集和逻辑数据集不适用这套 sheet。",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(XLSX_PATH) as zf:
        shared_strings = read_shared_strings(zf)
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: "xl/" + rel.attrib["Target"].lstrip("/")
            if not rel.attrib["Target"].startswith("xl/")
            else rel.attrib["Target"]
            for rel in rels
        }

        for sheet in workbook.find(f"{NS}sheets"):
            name = sheet.attrib["name"]
            target = rel_map[sheet.attrib[f"{RNS}id"]]
            rows = read_sheet(zf, target, shared_strings)
            fields, markers = parse_fields(rows)
            output = render_sheet(name, fields, markers)
            (OUT_DIR / ROUTES[name]).write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
