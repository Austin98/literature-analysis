# -*- coding: utf-8 -*-
"""公共工具: 读写 JSONL、加载检索配置(profile)、统一的记录结构"""
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows 控制台默认编码下中文输出会乱码
    _stream.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_profile(name_or_path):
    """profile 是一个 JSON 文件, 定义目标机构、关键词、承包商词表等。
    可以传内置名字(如 afrl_dayton)或任意路径"""
    p = Path(name_or_path)
    if not p.exists():
        p = PROFILES / f"{name_or_path}.json"
    if not p.exists():
        raise FileNotFoundError(f"找不到 profile: {name_or_path}")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()
