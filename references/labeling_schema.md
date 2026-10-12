# 语义标注字段定义

每条记录输出一行 JSON, 必须包含 `id`(与任务文件中的 id 一致)。

| 字段 | 类型 | 取值 | 说明 |
|---|---|---|---|
| id | string | 原样 | 与任务文件一致 |
| doc_type | string/null | article / review / conference / book chapter / report / preprint / other | 文献类型 |
| research_field | string/null | profile 中 topics 的一项 | 单标签主题归类, 依据标题与摘要 |
| topic_summary | string | 不超过 60 字 | 中文一句话概括研究内容 |
| is_target | bool/null | true / false | 作者单位是否属于目标机构, 依据首页原文 |
| evidence | string | 原文短句 | 判断依据, 无法判断时写明原因 |

规则:
- 不编造原文没有的信息; 首页和摘要都无法判断时, 对应字段填 null。
- 目标机构判断以首页作者单位为准, 资助致谢中提到的机构不算。
- research_field 必须取 profile 中 topics 里的值。
