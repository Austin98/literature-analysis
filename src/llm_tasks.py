# -*- coding: utf-8 -*-
"""语义标注: 由调用本 skill 的 AI 助手(如 Claude Code、Codex、CodeBuddy、Trae)完成, 不在代码里调用任何外部 API。

流程:
  1. prepare  把记录切成批次, 每批写一个 JSONL 任务文件(含标题、摘要、首页文本)
  2. (AI 助手) 读取每个批次文件, 按 references/labeling_schema.md 的字段逐条输出结果,
              写入 data/llm/out_XXX.jsonl(每行一个 JSON 对象, 含 id 字段)
  3. validate 校验输出: JSON 合法、id 完整、字段取值在允许范围内; 不合格的列出待重做
  4. merge    把校验通过的标注回填到清洗后的记录中

可选: 若要脱离 AI 助手在命令行批量运行, 可设置环境变量
  LLM_BASE_URL / LLM_API_KEY / LLM_MODEL (OpenAI 兼容协议), 再用 run 子命令。

用法:
  python src/llm_tasks.py prepare  --in data/clean.jsonl --outdir data/llm --batch 20
  python src/llm_tasks.py validate --outdir data/llm
  python src/llm_tasks.py merge    --in data/clean.jsonl --outdir data/llm --out data/labeled.jsonl
  python src/llm_tasks.py run      --outdir data/llm            # 需要 LLM_* 环境变量
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_jsonl  # noqa: E402

FIELDS_ALLOWED = {
    "research_field": None,  # 由 profile 的 topics 提供, 见 validate()
    "doc_type": {"article", "review", "conference", "book chapter", "report", "preprint", "other"},
    "is_target": {True, False, None},
}
PROMPT_HEAD = (
    "你是文献分析助手。对下面每条记录, 只依据给出的标题、摘要、首页文本作答, 不要编造。"
    "输出 JSONL: 每行一个对象, 必须包含 id 字段, 字段定义见 references/labeling_schema.md。"
    "无法判断时填 null, 并在 evidence 中写明依据。"
)


def prepare(rows, outdir, batch):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        tasks = [{
            "id": r.get("id") or r.get("doi") or r.get("title", "")[:40],
            "title": r.get("title", ""),
            "year": r.get("year"),
            "abstract": (r.get("abstract") or "")[:1500],
            "first_page": (r.get("text") or "")[:3000],
        } for r in chunk]
        p = outdir / f"task_{i // batch + 1:03d}.jsonl"
        write_jsonl(p, tasks)
        files.append(p.name)
    (outdir / "PROMPT.txt").write_text(PROMPT_HEAD, encoding="utf-8")
    print(f"生成 {len(files)} 个任务文件于 {outdir}")
    return files


def validate(outdir, expected_ids=None, topics=None):
    outdir = Path(outdir)
    errors, got = [], set()
    for f in sorted(outdir.glob("out_*.jsonl")):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{f.name}:{n} JSON 解析失败 {e}")
                continue
            if "id" not in o:
                errors.append(f"{f.name}:{n} 缺少 id")
                continue
            got.add(o["id"])
            if o.get("doc_type") is not None and o["doc_type"] not in FIELDS_ALLOWED["doc_type"]:
                errors.append(f"{o['id']}: doc_type 非法 {o['doc_type']!r}")
            if o.get("is_target") not in FIELDS_ALLOWED["is_target"]:
                errors.append(f"{o['id']}: is_target 非法 {o.get('is_target')!r}")
            if topics and o.get("research_field") not in (topics + [None]):
                errors.append(f"{o['id']}: research_field 不在主题体系内 {o.get('research_field')!r}")
    if expected_ids is not None:
        missing = set(expected_ids) - got
        if missing:
            errors.append(f"缺失 {len(missing)} 条标注, 例如 {sorted(missing)[:5]}")
    return errors


def merge(rows, outdir):
    outdir = Path(outdir)
    lab = {}
    for f in sorted(outdir.glob("out_*.jsonl")):
        for o in read_jsonl(f):
            lab[o["id"]] = o
    for r in rows:
        key = r.get("id") or r.get("doi") or r.get("title", "")[:40]
        o = lab.get(key)
        if o:
            for k, v in o.items():
                if k != "id":
                    r[f"llm_{k}"] = v
    return rows


def run_openai(outdir):
    """可选: 通过 OpenAI 兼容接口批量调用, 密钥只从环境变量读取"""
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("run 子命令需要 openai 包: pip install openai")
    base, key, model = os.environ.get("LLM_BASE_URL"), os.environ.get("LLM_API_KEY"), os.environ.get("LLM_MODEL")
    if not (base and key and model):
        sys.exit("请设置环境变量 LLM_BASE_URL、LLM_API_KEY、LLM_MODEL")
    client = OpenAI(base_url=base, api_key=key)
    prompt = (Path(outdir) / "PROMPT.txt").read_text(encoding="utf-8")
    schema = (Path(__file__).resolve().parent.parent / "references" / "labeling_schema.md").read_text(encoding="utf-8")
    for task in sorted(Path(outdir).glob("task_*.jsonl")):
        out = Path(outdir) / task.name.replace("task_", "out_")
        if out.exists():
            continue  # 断点续跑
        resp = client.chat.completions.create(
            model=model, temperature=0,
            messages=[{"role": "system", "content": prompt + "\n\n" + schema},
                      {"role": "user", "content": task.read_text(encoding="utf-8")}])
        out.write_text(resp.choices[0].message.content, encoding="utf-8")
        print("完成", out.name)


def main():
    ap = argparse.ArgumentParser(description="语义标注任务: prepare / validate / merge / run")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("prepare")
    p1.add_argument("--in", dest="inp", required=True)
    p1.add_argument("--outdir", required=True)
    p1.add_argument("--batch", type=int, default=20)
    p2 = sub.add_parser("validate")
    p2.add_argument("--outdir", required=True)
    p2.add_argument("--in", dest="inp")
    p2.add_argument("--profile")
    p3 = sub.add_parser("merge")
    p3.add_argument("--in", dest="inp", required=True)
    p3.add_argument("--outdir", required=True)
    p3.add_argument("--out", required=True)
    p4 = sub.add_parser("run")
    p4.add_argument("--outdir", required=True)
    a = ap.parse_args()

    if a.cmd == "prepare":
        prepare(read_jsonl(a.inp), a.outdir, a.batch)
    elif a.cmd == "validate":
        from common import load_profile
        topics = load_profile(a.profile).get("topics") if a.profile else None
        ids = [r.get("id") or r.get("doi") or r.get("title", "")[:40]
               for r in read_jsonl(a.inp)] if a.inp else None
        errs = validate(a.outdir, ids, topics)
        print("校验通过" if not errs else "\n".join(errs))
        sys.exit(1 if errs else 0)
    elif a.cmd == "merge":
        write_jsonl(a.out, merge(read_jsonl(a.inp), a.outdir))
        print(f"回填完成, 写入 {a.out}")
    else:
        run_openai(a.outdir)


if __name__ == "__main__":
    main()
