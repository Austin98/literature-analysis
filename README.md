# 文献分析 (literature-analysis)

一个 AI 编程助手的 skill (SKILL.md 格式)。给出主题、单位、作者、期刊或年份等任意条件, 自动完成:

检索或导入 → 去重 → 机构归属标注 → 首页信息抽取 → 语义分类 → 统计图表与 Markdown 报告

- 默认使用 OpenAlex 公开元数据, **无需任何账号**
- 也可导入 WoS / Scopus / CNKI / IEEE 导出的 RIS、BibTeX、CSV 文件
- 也可直接分析一个本地 PDF 文件夹
- 语义标注由调用它的 AI 助手完成, 仓库里**不包含任何 API 密钥**
- Python 脚本与工具无关, 只需安装 Python 3 及 requirements.txt 中的依赖; 语义标注步骤需要所用工具能读写文件

---

## 目录

1. [安装](#安装)
2. [快速开始 (几分钟跑通 demo)](#快速开始-几分钟跑通-demo)
3. [三种输入方式](#三种输入方式)
4. [完整流程与每一步的作用](#完整流程与每一步的作用)
5. [配置 profile](#配置-profile)
6. [语义标注详解](#语义标注详解)
7. [数据库账号与环境变量](#数据库账号与环境变量)
8. [输出说明](#输出说明)
9. [常见问题](#常见问题)
10. [展示品 (demo/)](#展示品-demo)
11. [测试](#测试)
12. [许可](#许可)

---

## 安装

### 1. 一句话安装 (推荐)

不用自己敲命令。把下面这句话直接发给你正在用的 AI 助手:

> 帮我安装 skill: 运行 `npx skills add Austin98/literature-analysis -g -y -a codebuddy`, 然后在安装目录下 `pip install -r requirements.txt`, 装好后读一下 SKILL.md, 告诉我怎么用。

助手会自己执行命令, 把 skill 装好并安装 Python 依赖。把 `-a codebuddy` 换成你用的工具:

| 你的工具 | 厂商 | `-a` 参数 |
|---|---|---|
| CodeBuddy | 腾讯 | `codebuddy` |
| Trae / Trae CN | 字节跳动 | `trae` / `trae-cn` |
| Qwen Code | 阿里通义 | `qwen-code` |
| 通义灵码 Lingma | 阿里 | `lingma` |
| Qoder / Qoder CN | 阿里 | `qoder` / `qoder-cn` |
| iFlow CLI | 心流 | `iflow-cli` |
| Kimi Code CLI | 月之暗面 | `kimi-code-cli` |
| CodeArts Agent | 华为 | `codearts-agent` |
| MiniMax Code | MiniMax | `minimax-code` |
| ZCode | 智谱 | `zcode` |
| Claude Code | Anthropic | `claude-code` |
| Codex CLI | OpenAI | `codex` |
| Cursor | Anysphere | `cursor` |
| Cline / Roo / Windsurf / opencode / GitHub Copilot 等 | — | 见 [CLI 支持列表](https://github.com/vercel-labs/skills) |
| 不确定, 或想装到所有工具 | — | 省略 `-a`(交互选择), 或写 `--all` |

> 工具名以 `skills` CLI 实际支持的为准 (`-a` 填错时 CLI 会列出全部可用值)。上表是国内常用的几个。

- `-g` 装到用户全局目录, 所有项目都能用; 去掉 `-g` 只装到当前项目。
- Python 依赖只在真正跑分析时才需要, 安装 skill 本身不需要。开始分析前记得装上 (见下一节)。

**实测记录** (Windows 11 + Git Bash, 从公开仓库安装)。测试机装了 Claude Code, 所以下面用它跑通; 换成上表任意 `-a` 参数命令完全一致:

| 项目 | 结果 |
|---|---|
| `npx skills add Austin98/literature-analysis -a claude-code -y` | 安装成功, 文件落到 `.agents/skills/` 并链接到 `.claude/skills/` |
| `python -m unittest discover tests` | 7 项全部通过 |
| `python src/report.py --in demo/data/clean.jsonl --outdir output` | 生成 `report.md` 与 5 张图, **无需联网、无需账号** |

### 2. 克隆仓库并安装依赖

想改代码或离线使用, 可以克隆下来:

```bash
git clone https://github.com/Austin98/literature-analysis.git
cd literature-analysis
pip install -r requirements.txt
```

依赖说明:

| 包 | 用途 |
|---|---|
| PyMuPDF | 读取 PDF 首页文本 |
| pandas, openpyxl | 表格数据处理 |
| matplotlib | 绘制图表 |
| requests | 调用 OpenAlex 接口 |

可选: 只有使用 `llm_tasks.py run` 子命令时才需要 `pip install openai`。

### 3. 用 skills CLI 自己安装 (命令行)

[vercel-labs/skills](https://github.com/vercel-labs/skills) 是通用的 skill 安装工具, 会自动把 skill 放到各个 AI 工具的目录中:

```bash
# 安装到当前项目 (交互式选择工具)
npx skills add Austin98/literature-analysis

# 指定工具安装到当前项目
npx skills add Austin98/literature-analysis -a codebuddy
npx skills add Austin98/literature-analysis -a trae -a qwen-code -a kimi-code-cli

# 安装到用户全局目录 (所有项目可用)
npx skills add Austin98/literature-analysis -g -a codebuddy

# 安装到所有支持的工具
npx skills add Austin98/literature-analysis --all

# 查看已安装的 skill / 删除
npx skills list
npx skills remove literature-analysis
```

`-a` 后面的工具名以 CLI 实际支持的为准, 完整列表运行 `npx skills add --help`, 或随便填一个错的名字让 CLI 把可用值列出来。常见的国产工具: `codebuddy`、`trae`、`trae-cn`、`qwen-code`、`lingma`、`qoder`、`qoder-cn`、`iflow-cli`、`kimi-code-cli`、`codearts-agent`、`minimax-code`、`zcode`; 国外工具: `claude-code`、`codex`、`cursor`、`gemini-cli`、`github-copilot`、`opencode`、`windsurf`、`cline`、`roo`。CLI 中没有列出的工具可使用下面的手动方式。

### 4. 不想安装? 用完即走

```bash
npx skills use Austin98/literature-analysis@literature-analysis
```

它会打印一段提示词, 并把 skill 的全部文件下载到临时目录, 提示词末尾会写明该目录的位置。把整段输出粘贴给任意 AI 助手就能直接使用, **不改动本机任何 skill 目录**。适合只想试一次、或在不方便安装的工具 (网页版等) 里使用的情况。

### 5. 手动安装 (任意工具)

只要工具支持 SKILL.md 格式的 skill 目录, 把整个 `literature-analysis` 文件夹复制到其 skill 目录即可。常见位置:

| 工具 | 个人(全局)目录 | 项目目录 |
|---|---|---|
| CodeBuddy | `~/.codebuddy/skills/literature-analysis/` | `.codebuddy/skills/literature-analysis/` |
| Trae / Trae CN | `~/.trae/skills/` (CN: `~/.trae-cn/skills/`) | `.trae/skills/literature-analysis/` |
| Qwen Code | `~/.qwen/skills/literature-analysis/` | `.qwen/skills/literature-analysis/` |
| 通义灵码 Lingma | `~/.lingma/skills/literature-analysis/` | `.lingma/skills/literature-analysis/` |
| Qoder | `~/.qoder/skills/` (CN: `~/.qoder-cn/skills/`) | `.qoder/skills/literature-analysis/` |
| iFlow CLI | `~/.iflow/skills/literature-analysis/` | `.iflow/skills/literature-analysis/` |
| Kimi Code CLI | `~/.agents/skills/literature-analysis/` | `.agents/skills/literature-analysis/` |
| CodeArts Agent | `~/.codeartsdoer/skills/literature-analysis/` | `.codeartsdoer/skills/literature-analysis/` |
| MiniMax Code | `~/.minimax/skills/literature-analysis/` | `.minimax/skills/literature-analysis/` |
| ZCode | `~/.zcode/skills/literature-analysis/` | `.zcode/skills/literature-analysis/` |
| Claude Code | `~/.claude/skills/literature-analysis/` | `.claude/skills/literature-analysis/` |
| Codex CLI | `~/.codex/skills/literature-analysis/` | `.agents/skills/literature-analysis/` |

- 上表目录取自 `skills` CLI 源码中的配置, 随版本可能变化。
- Windows 下 `~` 指 `%USERPROFILE%`, 例如 `C:\Users\<你>\.codebuddy\skills\literature-analysis\`。
- 各工具的目录约定可能随版本变化, 以该工具的官方文档为准。
- 若工具不支持 skill 目录, 可把 `SKILL.md` 的内容粘贴为其系统提示或项目规则, 并让它在仓库根目录执行其中的命令。脚本本身与工具无关。

### 6. 安装后怎么用

在 AI 助手中直接描述需求, 例如:

> 帮我分析 2022–2024 年 XX 大学关于钙钛矿太阳能电池的论文, 给出年度趋势、期刊分布和研究方向。

助手会读取 `SKILL.md`, 按其中的流程在 skill 目录下运行脚本。你也可以直接在终端中手动执行这些脚本 (见下文), 效果相同。

---

## 快速开始 (几分钟跑通 demo)

不需要账号。在仓库根目录执行:

```bash
# 1) 用 demo 配置从 OpenAlex 检索 2024 年钙钛矿文献 (最多 1000 条)
python src/search.py --profile profiles/demo_perovskite.json --max 1000 --mailto 你的邮箱 --out data/raw.jsonl

# 2) 去重
python src/clean.py --in data/raw.jsonl --out data/clean.jsonl

# 3) 生成统计报告 (此步不含语义标注, 研究方向一项会显示 "未标注")
python src/report.py --in data/clean.jsonl --outdir output --title "2024 钙钛矿太阳能电池文献分析"
```

完成后打开 `output/report.md` 查看报告, 图表在 `output/charts/`。
若想直接看成品, 参考仓库内的 `demo/report.md`。

> `--mailto` 可选。填写邮箱会让请求进入 OpenAlex 的"礼貌池", 速度更稳定。

---

## 三种输入方式

### 方式 1: OpenAlex 检索 (默认, 无需账号)

按关键词、机构、年份组合检索:

```bash
# 直接传参
python src/search.py --query "perovskite solar cell" --year-from 2024 --year-to 2024 --out data/raw.jsonl

# 按机构检索 (用 ROR ID)
python src/search.py --query "solar" --institution-ror https://ror.org/02e2egq70 --year-from 2022 --year-to 2024 --out data/raw.jsonl

# 使用 profile
python src/search.py --profile profiles/example_generic.json --out data/raw.jsonl
```

| 参数 | 说明 |
|---|---|
| `--profile` | profile JSON 路径, 或 `profiles/` 下的名字 (如 `demo_perovskite`) |
| `--query` | 关键词, 会覆盖 profile 中的 `query` |
| `--institution-ror` | 机构 ROR ID, 如 `https://ror.org/02e2egq70` |
| `--year-from` / `--year-to` | 年份区间 |
| `--max` | 最多取回的条数, 默认 2000 |
| `--mailto` | 邮箱, 进入礼貌池 (可选) |
| `--out` | 输出的 JSONL 文件 |

如何查 ROR ID: 打开 https://ror.org 搜索机构名称, 复制形如 `https://ror.org/xxxxxxxxx` 的 ID。

### 方式 2: 导入题录文件 (WoS / Scopus / CNKI / IEEE)

在数据库网页上导出题录, 再导入:

```bash
python src/import_records.py --ris 导出.ris --out data/raw.jsonl
python src/import_records.py --bib 导出.bib --out data/raw.jsonl
python src/import_records.py --csv 导出.csv --out data/raw.jsonl
```

三种格式互斥, 每次只能选一种。CSV 按以下列名读取 (大小写均可, 缺失则留空):

| 含义 | 可识别的列名 |
|---|---|
| 标题 | `Title` |
| DOI | `DOI` |
| 年份 | `Year`, `Publication Year` |
| 期刊 | `Source Title`, `Journal` |
| 作者 | `Authors` (以 `;` 分隔) |
| 单位 | `Affiliations`, `Affiliation` (以 `;` 分隔) |
| 被引 | `Cited by` |
| 摘要 | `Abstract` |

注意: 不同数据库导出的列名不完全一致, 若某列为空, 请检查导出文件的表头并按需调整。

### 方式 3: 本地 PDF 文件夹 (默认模式)

把一批 PDF 放在同一个文件夹中:

```bash
python src/import_records.py --pdf-dir ./papers --out data/raw.jsonl
python src/extract_pdf.py --in data/raw.jsonl --out data/with_text.jsonl
```

- 第一步把每个 PDF 登记为一条记录, 标题暂用文件名。
- 第二步读取每个 PDF 第 1 页的文本 (若第 1 页无文字则依次尝试第 2 页及末页), 供机构标注和语义标注使用。
- PDF 模式**不会**自动从首页解析出标题、年份、期刊等元数据。这些字段为空, 因此年度图和期刊图在该模式下信息较少。如需完整元数据, 请优先使用方式 1 或 2。
- 扫描版 PDF (无文字层) 无法抽取文本, 这类文件的机构标注与语义标注会缺失。

---

## 完整流程与每一步的作用

```bash
# 1. 获取原始记录 (三选一, 见上文), 输出 data/raw.jsonl

# 2. 抽取 PDF 首页文本 (仅 PDF 模式需要)
python src/extract_pdf.py --in data/raw.jsonl --out data/with_text.jsonl

# 3. 去重与机构标注
python src/clean.py --in data/with_text.jsonl --profile profiles/<name>.json --out data/clean.jsonl

# 4. 语义标注 (由 AI 助手完成, 见下一节)
python src/llm_tasks.py prepare  --in data/clean.jsonl --outdir data/llm --batch 20
#    ... AI 助手读取 data/llm/task_*.jsonl, 写出 data/llm/out_*.jsonl ...
python src/llm_tasks.py validate --outdir data/llm --in data/clean.jsonl --profile profiles/<name>.json
python src/llm_tasks.py merge    --in data/clean.jsonl --outdir data/llm --out data/labeled.jsonl

# 5. 统计图表与报告
python src/report.py --in data/labeled.jsonl --outdir output --title "某某主题文献分析"
```

各步说明:

- **extract_pdf.py**: 只对 PDF 模式需要。OpenAlex 与题录导入的记录已有摘要, 可跳过此步。
- **clean.py**: 按 DOI 与标题指纹去重。若提供 profile, 还会按 `target_patterns` / `contractor_patterns` 标注机构归属, 并**过滤掉资助、致谢中的机构** (例如 "supported by AFOSR" 不计为单位归属)。输出中的 `is_target` 表示是否命中目标机构。不加 `--profile` 时只去重。
- **llm_tasks.py prepare**: 把记录按 `--batch` 分批 (默认 20 条/批), 每批写一个 `task_NNN.jsonl`, 同时写 `PROMPT.txt`。
- **llm_tasks.py validate**: 检查 `out_*.jsonl` 是否合法 (JSON 格式、id 完整、字段取值在允许范围内、研究方向在 profile 的 `topics` 内)。不通过时列出具体错误, 退出码为 1, 只需重做报错的批次。
- **llm_tasks.py merge**: 把校验通过的标注以 `llm_` 前缀回填到记录中, 例如 `llm_research_field`。
- **report.py**: 生成 5 张图和 `report.md`。

---

## 配置 profile

profile 是一个 JSON 文件, 描述一次分析的检索条件与分类体系。字段:

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 否 | 配置名称 |
| `query` | 否 | 关键词 |
| `institution_ror` | 否 | 机构 ROR ID, 如 `https://ror.org/02e2egq70` |
| `year_from` / `year_to` | 否 | 年份区间 |
| `target_patterns` | 否 | 正则列表, 命中作者单位即标记为目标机构 |
| `contractor_patterns` | 否 | 正则列表, 标记合作方或承包商单位 |
| `topics` | 否 | 研究方向体系; 语义标注时只能从中选取 |

示例 (`profiles/example_generic.json`):

```json
{
  "name": "example_generic",
  "query": "machine learning",
  "year_from": 2023,
  "year_to": 2024,
  "target_patterns": ["Tsinghua University"],
  "contractor_patterns": [],
  "topics": ["方法与模型", "应用场景", "综述与其他"]
}
```

写 profile 的建议:

- 检索优先用 `institution_ror`, 比单位名称正则更稳定。`target_patterns` 用于识别作者单位文本。
- `topics` 建议 4–8 个, 互不重叠, 最后一项留作 "综述与其他"。
- 正则不区分大小写, 注意转义特殊字符。

仓库自带两个 profile:

- `example_generic.json`: 通用示例, 可复制后修改
- `demo_perovskite.json`: demo 使用的钙钛矿配置

---

## 语义标注详解

语义标注 (研究方向、文献类型、是否目标机构等) 由**调用本 skill 的 AI 助手**完成, 代码本身不调用任何外部大模型。

工作方式:

1. 运行 `prepare`, 生成 `data/llm/task_001.jsonl` 等任务文件。每条记录包含标题、年份、摘要 (截取 1500 字符) 与首页文本 (截取 3000 字符)。
2. 让 AI 助手读取任务文件, 按 `references/labeling_schema.md` 的字段为每条记录输出一行 JSON, 写入同名的 `out_NNN.jsonl`。每行必须含 `id`。
3. 运行 `validate` 检查结果。通过后运行 `merge` 回填。

标注规则 (详见 `references/labeling_schema.md`):

- 只依据标题、摘要、首页文本判断, **不得编造**。
- 无法判断的字段填 `null`, 并在 `evidence` 中说明依据。
- 资助、致谢中出现的机构**不计为单位归属**。
- `research_field` 只能从 profile 的 `topics` 中选择。

**给 AI 助手的提示示例**:

> 请读取 data/llm/task_001.jsonl, 按 references/labeling_schema.md 的字段为每条记录写出 data/llm/out_001.jsonl, 每行一个 JSON。完成后运行 validate, 有错误就只重做报错的批次。

若想脱离 AI 助手, 在命令行批量完成标注, 可使用 `run` 子命令。它通过 OpenAI 兼容接口调用模型, 需要先设置环境变量:

```bash
pip install openai
export LLM_BASE_URL=https://api.example.com/v1   # 接口地址
export LLM_API_KEY=你的密钥                       # 只从环境变量读取, 不写入文件
export LLM_MODEL=模型名称
python src/llm_tasks.py run --outdir data/llm
```

`run` 会跳过已有的 `out_*.jsonl`, 中断后可以继续运行。完成后同样执行 `validate` 与 `merge`。

---

## 数据库账号与环境变量

**脚本不读取也不保存任何数据库账号。** 需要 WoS、Scopus 等库时, 在其网页端导出题录, 再用方式 2 导入即可。

如确实需要通过环境变量配置 LLM 接口:

1. 复制 `.env.example` 为 `.env`, 填写其中的值。
2. `.env` 已列入 `.gitignore`, 不会被提交到 GitHub。
3. 也可以直接在终端中 `export` 同名变量, 不必创建 `.env`。

`.env.example` 中的变量:

| 变量 | 用途 |
|---|---|
| `LLM_BASE_URL` | OpenAI 兼容接口地址 (仅 `run` 子命令) |
| `LLM_API_KEY` | 接口密钥 (仅 `run` 子命令) |
| `LLM_MODEL` | 模型名称 (仅 `run` 子命令) |
| `WOS_API_KEY`, `SCOPUS_API_KEY` | 预留, 当前版本未使用 |

**安全提示**: 不要把密钥写进 profile、脚本或聊天记录中。如果密钥曾经泄露, 请立即在对应平台撤销并重新生成。

---

## 输出说明

运行 `report.py` 后, 输出目录结构如下:

```
output/
├── report.md              # Markdown 报告 (统计口径、各类计数、图表引用)
└── charts/
    ├── 01_年度分布.png
    ├── 02_期刊Top15.png
    ├── 03_研究方向.png     # 需完成语义标注才有实际分类
    ├── 04_文献类型.png     # 需完成语义标注才有实际分类
    └── 05_合作机构Top15.png
```

- 报告开头列出 "记录总数" 与 "纳入分析" 篇数; 之后依次为年度分布、期刊 Top15、研究方向、高被引 Top10, 文末嵌入图表。
- `report.md` **不会**自动写出去重规则或标注是否完成, 这些需要你在结论中自行说明。
- 若没有任何记录命中 `target_patterns` (即 `is_target` 全为假), `report.py` 会退回到分析全部记录, 请注意核对 "纳入分析" 的数字。
- 图表使用 Microsoft YaHei 或 SimHei 字体显示中文; 若系统中两者都没有, 中文可能显示为方框。
- 研究方向一项若显示为 "未标注", 说明尚未完成语义标注, 不应作为结论。

---

## 常见问题

**Q: 检索结果为 0 条?**
检查关键词拼写, 尽量使用英文; 检查年份区间; 若使用 `--institution-ror`, 确认 ROR ID 正确。

**Q: 机构标注结果为空?**
OpenAlex 数据中的单位字段可能不完整。可以补充 `target_patterns` 的正则, 或改用 `--institution-ror` 检索。

**Q: 研究方向那张图全是 "未标注"?**
说明没有完成语义标注。按上文 "语义标注详解" 完成 `prepare → 标注 → validate → merge` 后再运行 `report.py`。

**Q: PDF 文件夹模式的标题、年份都是空的?**
这是设计如此: 该模式只抽取首页文本, 不解析元数据。需要完整信息请使用题录导入或 OpenAlex 检索。

**Q: 中文报告的图表显示为方框?**
系统缺少 Microsoft YaHei 与 SimHei 字体。请安装其中之一。

**Q: 控制台中文乱码?**
脚本已在 `common.py` 中把输出编码设为 UTF-8。若仍乱码, 请在终端中执行 `chcp 65001` 后再运行。

**Q: `run` 子命令报错 "需要 openai 包"?**
执行 `pip install openai`。它是可选依赖, 只有 `run` 子命令需要。

**Q: 运行时出现 "请设置环境变量 LLM_BASE_URL..."?**
`run` 子命令必须设置三个 LLM 变量。若只用 AI 助手完成标注, 无需设置。

---

## 展示品 (demo/)

`demo/` 是一个完整运行结果: 2024 年钙钛矿太阳能电池文献, 数据来自 OpenAlex 公开元数据 (无全文, 无 PDF)。

- `demo/report.md`: 报告
- `demo/charts/`: 图表
- `demo/data/clean.jsonl`: 去重后的 980 条题录记录

**注意**: 本 demo 只做了检索、去重和统计, **未运行语义标注**, 因此报告中 "研究方向" 一项全部为 "未标注"。跑完标注后可重新执行 `report.py` 得到完整版本。

复现:

```bash
python src/search.py --profile profiles/demo_perovskite.json --max 1000 --mailto 你的邮箱 --out data/raw.jsonl
python src/clean.py --in data/raw.jsonl --out data/clean.jsonl
python src/report.py --in data/clean.jsonl --outdir output --title "2024 钙钛矿太阳能电池文献分析"
```

---

## 测试

```bash
python -m unittest discover tests
```

测试使用合成数据, 不需要网络、PDF 或账号。覆盖: 去重、机构与资助过滤、RIS 与 BibTeX 解析、摘要还原、标注校验与回填。

---

## 许可

MIT, 见 LICENSE。
