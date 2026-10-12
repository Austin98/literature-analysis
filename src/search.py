# -*- coding: utf-8 -*-
"""检索: 从 OpenAlex 按条件检索题录(公开、免费、无需账号)。

可选的其它数据库(WoS、Scopus、CNKI 等)需要账号时, 请先导出为 RIS/BibTeX/CSV,
再用 import_records.py 导入, 不把账号写入代码。

用法:
  python src/search.py --profile profiles/example_generic.json --out data/raw.jsonl
  python src/search.py --institution-ror https://ror.org/02e2egq70 --year-from 2025 --out data/raw.jsonl
"""
import argparse
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_profile, write_jsonl  # noqa: E402

API = "https://api.openalex.org/works"
FIELDS = "id,doi,title,publication_year,type,cited_by_count,primary_location,authorships,abstract_inverted_index,keywords,topics"


def abstract_text(inv):
    """OpenAlex 摘要是倒排索引, 还原为文本"""
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def to_record(w):
    src = (w.get("primary_location") or {}).get("source") or {}
    authors, affils = [], []
    for a in w.get("authorships", []):
        authors.append(a.get("author", {}).get("display_name", ""))
        for inst in a.get("institutions", []):
            affils.append({"author": a.get("author", {}).get("display_name", ""),
                           "name": inst.get("display_name", ""),
                           "country": inst.get("country_code", ""),
                           "ror": inst.get("ror", "")})
    return {
        "id": w.get("id", ""),
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "title": w.get("title") or "",
        "year": w.get("publication_year"),
        "type": w.get("type", ""),
        "journal": src.get("display_name", ""),
        "cited_by": w.get("cited_by_count", 0),
        "authors": authors,
        "affiliations": affils,
        "abstract": abstract_text(w.get("abstract_inverted_index")),
        "keywords": [k.get("display_name", "") for k in w.get("keywords", [])],
        "topics": [t.get("display_name", "") for t in w.get("topics", [])[:3]],
    }


def build_filter(profile):
    f = []
    if profile.get("year_from") and profile.get("year_to"):
        f.append(f"publication_year:{profile['year_from']}-{profile['year_to']}")
    elif profile.get("year_from"):
        f.append(f"publication_year:>{profile['year_from'] - 1}")
    if profile.get("institution_ror"):
        f.append(f"authorships.institutions.ror:{profile['institution_ror']}")
    if profile.get("journal_id"):
        f.append(f"primary_location.source.id:{profile['journal_id']}")
    return ",".join(f)


def search(profile, mailto=None, max_records=2000):
    params = {"per-page": 200, "select": FIELDS, "cursor": "*"}
    flt = build_filter(profile)
    if flt:
        params["filter"] = flt
    if profile.get("query"):
        params["search"] = profile["query"]
    if mailto:
        params["mailto"] = mailto
    out = []
    while len(out) < max_records:
        r = requests.get(API, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        out.extend(to_record(w) for w in data.get("results", []))
        nxt = data.get("meta", {}).get("next_cursor")
        if not nxt or not data.get("results"):
            break
        params["cursor"] = nxt
        time.sleep(0.2)
    return out[:max_records]


def main():
    ap = argparse.ArgumentParser(description="按条件从 OpenAlex 检索题录")
    ap.add_argument("--profile", help="profile JSON 路径或内置名")
    ap.add_argument("--query", help="关键词(覆盖 profile)")
    ap.add_argument("--institution-ror", help="机构 ROR, 如 https://ror.org/02e2egq70")
    ap.add_argument("--year-from", type=int)
    ap.add_argument("--year-to", type=int)
    ap.add_argument("--max", type=int, default=2000)
    ap.add_argument("--mailto", help="邮箱, 进入 OpenAlex 礼貌池(可选)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    prof = load_profile(a.profile) if a.profile else {}
    for key, val in (("query", a.query), ("institution_ror", a.institution_ror),
                     ("year_from", a.year_from), ("year_to", a.year_to)):
        if val is not None:
            prof[key] = val
    if not any(prof.get(k) for k in ("query", "institution_ror", "journal_id")):
        ap.error("至少需要 --query、--institution-ror 或 profile 中的一项条件")

    rows = search(prof, mailto=a.mailto, max_records=a.max)
    write_jsonl(a.out, rows)
    print(f"检索到 {len(rows)} 条, 写入 {a.out}")


if __name__ == "__main__":
    main()
