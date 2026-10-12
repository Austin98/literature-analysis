# -*- coding: utf-8 -*-
"""统计与出图: 年度分布、期刊 Top、研究方向分布、被引 Top, 输出 Markdown 报告与图表。

用法:
  python src/report.py --in data/labeled.jsonl --outdir output [--title "文献分析报告"]
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def bar(counter, title, path, horizontal=False, top=15):
    items = counter.most_common(top)[::-1] if horizontal else sorted(counter.items())
    if not items:
        return False
    labels, vals = zip(*items)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    if horizontal:
        ax.barh([str(l)[:40] for l in labels], vals, color="#3a6ea5")
    else:
        ax.bar([str(l) for l in labels], vals, color="#3a6ea5")
        plt.xticks(rotation=0)
    ax.set_title(title)
    for i, v in enumerate(vals):
        if horizontal:
            ax.text(v, i, f" {v}", va="center", fontsize=8)
        else:
            ax.text(i, v, str(v), ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def main():
    ap = argparse.ArgumentParser(description="统计并生成图表与 Markdown 报告")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--title", default="文献分析报告")
    a = ap.parse_args()

    rows = read_jsonl(a.inp)
    out = Path(a.outdir)
    (out / "charts").mkdir(parents=True, exist_ok=True)
    target = [r for r in rows if r.get("is_target")] or rows

    years = Counter(r["year"] for r in target if r.get("year"))
    journals = Counter(r["journal"] for r in target if r.get("journal"))
    fields = Counter(r.get("llm_research_field") or "未标注" for r in target)
    types = Counter(r.get("llm_doc_type") or "未标注" for r in target)
    partners = Counter(a_["name"] for r in target for a_ in r.get("affiliations", [])
                       if a_.get("name") and not r.get("is_target"))

    charts = [
        (years, "年度发文量", "01_年度分布.png", False),
        (journals, "期刊来源 Top15", "02_期刊Top15.png", True),
        (fields, "研究方向分布", "03_研究方向.png", True),
        (types, "文献类型分布", "04_文献类型.png", False),
        (partners, "合作机构 Top15", "05_合作机构Top15.png", True),
    ]
    made = [name for c, t, name, h in charts if bar(c, t, out / "charts" / name, horizontal=h)]

    top_cited = sorted(target, key=lambda r: r.get("cited_by") or 0, reverse=True)[:10]
    lines = [f"# {a.title}", "", f"- 记录总数: {len(rows)}", f"- 纳入分析: {len(target)}", ""]
    lines += ["## 一、年度分布", "", "| 年份 | 篇数 |", "|---|---|"]
    lines += [f"| {y} | {n} |" for y, n in sorted(years.items())]
    lines += ["", "## 二、期刊来源 Top15", "", "| 期刊 | 篇数 |", "|---|---|"]
    lines += [f"| {j} | {n} |" for j, n in journals.most_common(15)]
    lines += ["", "## 三、研究方向", "", "| 方向 | 篇数 |", "|---|---|"]
    lines += [f"| {k} | {n} |" for k, n in fields.most_common()]
    lines += ["", "## 四、高被引 Top10", "", "| 标题 | 年份 | 被引 |", "|---|---|---|"]
    lines += [f"| {r['title'][:70]} | {r.get('year')} | {r.get('cited_by', 0)} |" for r in top_cited]
    lines += ["", "## 附图", ""]
    lines += [f"![{n}](charts/{n})" for n in made]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"报告 {out / 'report.md'}, 图表 {len(made)} 张")


if __name__ == "__main__":
    main()
