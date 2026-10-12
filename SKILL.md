---
name: literature-analysis
description: 面向任意条件的文献自动分析。给出主题、单位(机构)、作者、期刊或年份区间, 从 OpenAlex 检索或导入 WoS/Scopus/CNKI/IEEE 导出文件或本地 PDF 文件夹, 完成去重、机构归属标注、首页文本抽取、由当前 AI 助手做语义分类, 最后生成统计图表与 Markdown 报告。当用户提到文献分析、文献综述统计、论文计量、某机构/某主题近几年论文盘点时使用。
---

# 文献分析 (literature-analysis)

## 适用场景

- 按主题、单位、作者、期刊、年份任意组合检索并统计文献
- 把已有的 WoS / Scopus / CNKI / IEEE 导出文件(RIS、BibTeX、CSV)做同样的分析
- 整理一个本地 PDF 文件夹, 自动抽取首页信息并分类

## 工作流程

在 skill 目录下执行(下文 `$SKILL` 指 skill 所在目录, 即安装位置, 见 README 的安装表):

1. **确定输入来源**(三选一)
   - OpenAlex 检索(默认, 无需账号):
     `python src/search.py --profile profiles/<name>.json --out data/raw.jsonl`
     也可以直接传参: `--query "..." --institution-ror https://ror.org/xxxx --year-from 2022 --year-to 2024`
   - 题录文件导入: `python src/import_records.py --ris|--bib|--csv <文件> --out data/raw.jsonl`
   - PDF 文件夹(默认模式): `python src/import_records.py --pdf-dir <文件夹> --out data/raw.jsonl`
2. **PDF 首页文本**(有 PDF 时): `python src/extract_pdf.py --in data/raw.jsonl --out data/with_text.jsonl`
3. **清洗与机构标注**: `python src/clean.py --in data/with_text.jsonl --profile profiles/<name>.json --out data/clean.jsonl`
   (profile 可省略, 此时只做去重)
4. **语义标注(由当前 AI 助手完成, 不调用外部 API)**
   - `python src/llm_tasks.py prepare --in data/clean.jsonl --outdir data/llm --batch 20`
   - 逐个读取 `data/llm/task_NNN.jsonl`, 按 `references/labeling_schema.md` 的字段为每条记录写出
     `data/llm/out_NNN.jsonl`(每行一个 JSON, 必须含 `id`)。研究方向只能从 profile 的 `topics` 中选; 无法判断填 `null`, 不得编造。
   - `python src/llm_tasks.py validate --outdir data/llm --in data/clean.jsonl --profile profiles/<name>.json`
     校验不通过则只重做报错的批次
   - `python src/llm_tasks.py merge --in data/clean.jsonl --outdir data/llm --out data/labeled.jsonl`
   - 若用户希望脱离 AI 助手在命令行批量跑, 可设置 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 后使用 `run` 子命令(OpenAI 兼容接口, 密钥只从环境变量读取)
5. **统计出图与报告**: `python src/report.py --in data/labeled.jsonl --outdir output --title "<报告标题>"`
   输出 `output/report.md` 与 `output/charts/*.png`

## 关键约定

- **不硬编码任何密钥**。数据库账号只通过环境变量或 `.env` 提供, 仓库中只保留 `.env.example`(仅变量名)。
- **语义判断只依据标题、摘要、首页文本**。资助/致谢中的机构不计为单位归属(`clean.py` 已做句子级过滤)。
- **写 profile 时**: 机构用 ROR ID 检索最稳; 作者单位正则写入 `target_patterns`, 合作方写入 `contractor_patterns`。
- 报告中的统计口径(纳入篇数、去重规则、标注是否完成)需要在最终结论里说明, 不要把未标注的类别当作结论。

## 目录

- `src/` 各步骤脚本, 均为单文件 CLI
- `profiles/` 检索配置(JSON), `example_generic.json` 为通用示例
- `references/labeling_schema.md` 语义标注字段定义
- `demo/` 展示品: 2024 年钙钛矿太阳能电池文献(OpenAlex 公开元数据), 含图表与报告
- `tests/` 使用合成数据的单元测试, 运行 `python -m unittest discover tests`
