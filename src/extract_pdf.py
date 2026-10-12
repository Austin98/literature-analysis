# -*- coding: utf-8 -*-
"""PDF 抽取: 读取每篇 PDF 的首页(版式特殊时回退第2页或末页)文本, 写入记录的 text 字段。

用法:
  python src/extract_pdf.py --in data/raw.jsonl --out data/with_text.jsonl
"""
import argparse
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_jsonl  # noqa: E402

INST_HINT = re.compile(
    r"(?i)(university|universit|institute|laborator|college|academy|hospital|school\b|"
    r"center|centre|directorate|wing\b|foundation|corporation|corp\.|inc\b|llc|gmbh|ltd|"
    r"department of|dept\.? of|air force|army|navy|nasa)"
)


def page_text(doc, idx):
    return doc[idx].get_text("text") if 0 <= idx < doc.page_count else ""


def first_page_text(path):
    """首页文本; 首页没有机构特征行时补第2页, 末页机构行较多时(如 Springer 版式)补末页"""
    with fitz.open(path) as doc:
        first = page_text(doc, 0)
        if len(INST_HINT.findall(first)) >= 1 or doc.page_count == 1:
            return first
        second = page_text(doc, 1)
        if len(INST_HINT.findall(second)) >= 1:
            return first + "\n" + second
        last = page_text(doc, doc.page_count - 1)
        if len(INST_HINT.findall(last)) >= 2:
            return first + "\n@@@@@\n" + last
        return first


def main():
    ap = argparse.ArgumentParser(description="抽取 PDF 首页文本")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = read_jsonl(a.inp)
    n = 0
    for r in rows:
        if not r.get("pdf"):
            continue
        p = Path(r["pdf"])
        try:
            r["text"] = first_page_text(p)
            n += 1
        except Exception as e:  # 损坏或加密的 PDF 不中断整个批次
            r["text"] = ""
            r["extract_error"] = str(e)
    write_jsonl(a.out, rows)
    print(f"抽取 {n}/{len(rows)} 篇 PDF 首页文本, 写入 {a.out}")


if __name__ == "__main__":
    main()
