# 文献分析 (literature-analysis)

一个 AI 编程助手的 skill(SKILL.md 格式): 给出主题、单位、作者、期刊或年份等任意条件, 自动完成文献检索/导入、去重、
机构归属标注、首页信息抽取、语义分类, 并生成统计图表与 Markdown 报告。

- 默认使用 OpenAlex 公开元数据, 无需任何账号
- 也可导入 WoS / Scopus / CNKI / IEEE 导出的 RIS、BibTeX、CSV 文件
- 也可直接分析一个本地 PDF 文件夹
- 语义标注由调用它的 AI 助手完成, 仓库里不包含任何 API 密钥
- Python 脚本与工具无关, 只要能运行 Python 3.10+ 即可; 语义标注步骤需要所用工具能读写文件

## 安装

先克隆仓库, 再把整个文件夹放到所用工具的 skill 目录中:

```bash
git clone https://github.com/Austin98/literature-analysis.git
pip install -r literature-analysis/requirements.txt
```

| 工具 | 个人(全局)目录 | 项目目录 |
|---|---|---|
| Claude Code | `~/.claude/skills/literature-analysis/` | `.claude/skills/literature-analysis/` |
| Codex CLI | `~/.codex/skills/literature-analysis/` | `.codex/skills/literature-analysis/` |
| CodeBuddy | `~/.codebuddy/skills/literature-analysis/` | `.codebuddy/skills/literature-analysis/` |
| Trae | `~/.trae/skills/literature-analysis/` | `.trae/skills/literature-analysis/` |

Windows 下 `~` 指 `%USERPROFILE%`。各工具的目录约定可能随版本变化, 以该工具的官方文档为准。

表中没有的工具: 只要它支持 SKILL.md 格式的 skill 目录, 就把整个文件夹放进它的 skill 目录即可。
如果它不支持 skill, 可以把 `SKILL.md` 的内容作为系统提示或项目规则, 再让它在仓库根目录执行其中的命令。
核心脚本只依赖 Python 3.10+ 和 `requirements.txt`, 不依赖任何特定工具。
也可以用 `npx skills add Austin98/literature-analysis --agent <工具名>` 安装(取决于 vercel-labs/skills CLI 对该工具的支持)。

安装后在对话中直接描述需求即可, 例如 "帮我分析 2022–2024 年 XX 大学关于钙钛矿的论文"。

## 三种输入方式

```bash
# 1) OpenAlex 检索(可直接传参, 也可写 profile)
python src/search.py --query "perovskite solar cell" --year-from 2024 --year-to 2024 --out data/raw.jsonl
python src/search.py --profile profiles/example_generic.json --out data/raw.jsonl

# 2) 题录文件导入
python src/import_records.py --ris 导出.ris --out data/raw.jsonl

# 3) PDF 文件夹(默认模式)
python src/import_records.py --pdf-dir ./papers --out data/raw.jsonl
python src/extract_pdf.py --in data/raw.jsonl --out data/with_text.jsonl
```

## 完整流程

```bash
python src/clean.py --in data/with_text.jsonl --profile profiles/<name>.json --out data/clean.jsonl
python src/llm_tasks.py prepare  --in data/clean.jsonl --outdir data/llm --batch 20
# AI 助手读取 data/llm/task_*.jsonl, 写出 data/llm/out_*.jsonl (字段见 references/labeling_schema.md)
python src/llm_tasks.py validate --outdir data/llm --in data/clean.jsonl --profile profiles/<name>.json
python src/llm_tasks.py merge    --in data/clean.jsonl --outdir data/llm --out data/labeled.jsonl
python src/report.py --in data/labeled.jsonl --outdir output --title "某某主题文献分析"
```

输出: `output/report.md` 与 `output/charts/` 下的 5 张图(年度、期刊 Top15、研究方向、文献类型、合作机构 Top15)。

## 配置 profile

profile 是 JSON 文件, 字段说明:

| 字段 | 说明 |
|---|---|
| `query` | 关键词 |
| `institution_ror` | 机构 ROR ID, 如 `https://ror.org/02e2egq70`; 查询机构 ID 可用 ror.org 或 OpenAlex |
| `year_from` / `year_to` | 年份区间 |
| `target_patterns` | 正则, 命中作者单位即标记为目标机构 |
| `contractor_patterns` | 正则, 标记合作方/承包商单位 |
| `topics` | 研究方向体系, 语义标注时只能从中选取 |

示例见 `profiles/example_generic.json`。

## 数据库账号

脚本不读取也不保存任何数据库账号。需要 WoS、Scopus 等库时, 在其网页端导出题录再用导入模式处理。
如需设置 LLM 后端的环境变量, 复制 `.env.example` 为 `.env` 填写; `.env` 已在 `.gitignore` 中。

## 展示品 (demo/)

`demo/` 是一个完整运行结果: 2024 年钙钛矿太阳能电池文献, 数据来自 OpenAlex 公开元数据(无全文, 无 PDF)。

- `demo/report.md` 报告
- `demo/charts/` 图表
- `demo/data/clean.jsonl` 去重后的题录记录

注意: 本 demo 只做了检索、去重和统计, **未运行语义标注**, 因此报告中 "研究方向" 一项全部为 "未标注"。
跑完标注后可重新执行 `report.py` 得到完整版本。

复现: `python src/search.py --profile profiles/demo_perovskite.json --max 1000 --mailto <你的邮箱> --out data/raw.jsonl`, 再执行 `clean.py` 去重

## 测试

```bash
python -m unittest discover tests
```

测试使用合成数据, 不需要网络、PDF 或账号。

## 许可

MIT, 见 LICENSE。
