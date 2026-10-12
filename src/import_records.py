# -*- coding: utf-8 -*-
"""导入: 把本地题录文件(RIS / BibTeX / CSV)或 PDF 文件夹转为统一的 JSONL。

用于 WoS、Scopus、CNKI、IEEE 等库导出的文件, 不需要在代码里写任何账号。

用法:
  python src/import_records.py --ris 导出.ris --out data/raw.jsonl
  python src/import_records.py --bib 导出.bib --out data/raw.jsonl
  python src/import_records.py --csv 导出.csv --out data/raw.jsonl
  python src/import_records.py --pdf-dir ./papers --out data/raw.jsonl
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import clean, write_jsonl  # noqa: E402


def empty(title=""):
    return {"id": "", "doi": "", "title": title, "year": None, "type": "",
            "journal": "", "cited_by": 0, "authors": [], "affiliations": [],
            "abstract": "", "keywords": [], "topics": [], "pdf": ""}


def parse_ris(text):
    recs, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur = empty()
        elif tag == "ER":
            if cur:
                recs.append(cur)
            cur = None
        elif cur is not None:
            if tag in ("TI", "T1") and not cur["title"]:
                cur["title"] = val
            elif tag in ("AU", "A1"):
                cur["authors"].append(val)
            elif tag in ("AD", "C1", "C3"):
                cur["affiliations"].append({"author": "", "name": val, "country": "", "ror": ""})
            elif tag in ("PY", "Y1") and not cur["year"]:
                m2 = re.search(r"(\d{4})", val)
                cur["year"] = int(m2.group(1)) if m2 else None
            elif tag in ("JO", "JF", "T2") and not cur["journal"]:
                cur["journal"] = val
            elif tag == "DO":
                cur["doi"] = val
            elif tag == "AB":
                cur["abstract"] = val
            elif tag == "KW":
                cur["keywords"].append(val)
            elif tag == "TY":
                cur["type"] = val
    return recs


def parse_bib(text):
    recs = []
    for block in re.split(r"(?=^@\w+\s*\{)", text, flags=re.M):
        if not block.lstrip().startswith("@"):
            continue
        fields = dict(re.findall(r"(\w+)\s*=\s*[{\"](.*?)[}\"]\s*,?\s*$", block, flags=re.M | re.S))
        fields = {k.lower(): clean(v) for k, v in fields.items()}
        r = empty(fields.get("title", ""))
        r["authors"] = [a.strip() for a in re.split(r"\s+and\s+", fields.get("author", "")) if a.strip()]
        r["affiliations"] = [{"author": "", "name": fields["affiliation"], "country": "", "ror": ""}] \
            if fields.get("affiliation") else []
        r["year"] = int(fields["year"]) if fields.get("year", "").isdigit() else None
        r["journal"] = fields.get("journal", fields.get("booktitle", ""))
        r["doi"] = fields.get("doi", "")
        r["abstract"] = fields.get("abstract", "")
        recs.append(r)
    return recs


def parse_csv(path):
    recs = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            r = empty(row.get("Title") or row.get("title") or "")
            r["doi"] = row.get("DOI") or row.get("doi") or ""
            y = row.get("Year") or row.get("year") or row.get("Publication Year") or ""
            r["year"] = int(y) if str(y).isdigit() else None
            r["journal"] = row.get("Source Title") or row.get("Journal") or row.get("journal") or ""
            au = row.get("Authors") or row.get("authors") or ""
            r["authors"] = [a.strip() for a in re.split(r";|\band\b", au) if a.strip()]
            af = row.get("Affiliations") or row.get("affiliations") or row.get("Affiliation") or ""
            r["affiliations"] = [{"author": "", "name": a.strip(), "country": "", "ror": ""}
                                 for a in af.split(";") if a.strip()]
            c = row.get("Cited by") or row.get("cited_by") or "0"
            r["cited_by"] = int(c) if str(c).isdigit() else 0
            r["abstract"] = row.get("Abstract") or row.get("abstract") or ""
            recs.append(r)
    return recs


def from_pdf_dir(folder):
    """PDF 文件夹模式: 每个 PDF 一条记录, 文本留给 extract_pdf.py 补全"""
    recs = []
    for p in sorted(Path(folder).rglob("*.pdf")):
        r = empty(p.stem)
        r["id"] = p.stem
        r["pdf"] = str(p.resolve())
        recs.append(r)
    return recs


def main():
    ap = argparse.ArgumentParser(description="导入题录文件或 PDF 文件夹")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ris")
    g.add_argument("--bib")
    g.add_argument("--csv")
    g.add_argument("--pdf-dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.ris:
        recs = parse_ris(Path(a.ris).read_text(encoding="utf-8-sig"))
    elif a.bib:
        recs = parse_bib(Path(a.bib).read_text(encoding="utf-8-sig"))
    elif a.csv:
        recs = parse_csv(a.csv)
    else:
        recs = from_pdf_dir(a.pdf_dir)
    write_jsonl(a.out, recs)
    print(f"导入 {len(recs)} 条, 写入 {a.out}")


if __name__ == "__main__":
    main()
