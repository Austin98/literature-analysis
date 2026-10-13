# -*- coding: utf-8 -*-
"""清洗: 去重(DOI / 标题指纹) + 按 profile 做机构归属标注。

profile 中可选字段:
  target_patterns    正则列表, 命中作者单位即标记为目标机构(如 "Tsinghua University")
  contractor_patterns 正则列表, 标记承包商/合作方单位

用法:
  python src/clean.py --in data/raw.jsonl --profile profiles/example_generic.json --out data/clean.jsonl
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_profile, read_jsonl, write_jsonl  # noqa: E402


def fingerprint(title):
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())[:80]


def dedup(rows):
    seen_doi, seen_title, out = set(), set(), []
    for r in rows:
        doi = (r.get("doi") or "").lower().strip()
        fp = fingerprint(r.get("title"))
        if (doi and doi in seen_doi) or (fp and fp in seen_title):
            continue
        if doi:
            seen_doi.add(doi)
        if fp:
            seen_title.add(fp)
        out.append(r)
    return out


def _any(patterns, text):
    return [p for p in patterns if re.search(p, text, re.I)]


def annotate(rows, profile):
    tgt = profile.get("target_patterns", [])
    con = profile.get("contractor_patterns", [])
    for r in rows:
        names = [a.get("name", "") for a in r.get("affiliations", [])]
        text = " | ".join(names) + " | " + (r.get("text") or "")
        # 句子级排除: 含资助/致谢词的句子不计入归属, 避免 "supported by AFOSR" 误标
        sents = [s for s in re.split(r"(?<=[.!?])\s+", text)
                 if not re.search(r"(?i)fund|grant|support|acknowledg|sponsor", s)]
        clean_text = " ".join(sents)
        r["target_hits"] = _any(tgt, clean_text) if tgt else []
        r["contractor_hits"] = _any(con, clean_text) if con else []
        r["is_target"] = bool(r["target_hits"])
    return rows


def main():
    ap = argparse.ArgumentParser(description="去重并按 profile 标注机构归属")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--profile")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = read_jsonl(a.inp)
    before = len(rows)
    rows = dedup(rows)
    if a.profile:
        rows = annotate(rows, load_profile(a.profile))
    write_jsonl(a.out, rows)
    n_t = sum(1 for r in rows if r.get("is_target"))
    print(f"去重 {before} -> {len(rows)}; 目标机构标注 {n_t} 篇; 写入 {a.out}")


if __name__ == "__main__":
    main()
