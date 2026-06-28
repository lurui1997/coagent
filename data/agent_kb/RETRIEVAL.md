# RAG 知识库检索规则

`rag-bot` 使用 **加权评分检索**，非简单关键词包含。配置见 `index_meta.json`，条目见 `faq.json`。

## 1. 条目 Schema

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 唯一 ID，如 `faq-shipping-001` |
| `category` | ✅ | 类目：`售后` / `物流` / `会员` / `支付` / `账户` / `合规` |
| `question` | ✅ | 标准问法 |
| `answer` | ✅ | 权威答复（RAG 唯一依据） |
| `keywords` | ✅ | 主关键词（query 子串匹配） |
| `synonyms` | 建议 | 同义词（query 子串匹配，权重低于 keywords） |
| `tags` | 建议 | 场景标签，用于类目加分 |
| `priority` | 可选 | 1–5，同分时优先（默认 3） |
| `enabled` | 可选 | 默认 `true`；`false` 不参与检索 |

## 2. 评分公式

对每条 enabled 条目计算 `score ∈ [0, 1]`（实现见 `agents/kb_retrieval.py`）：

| 信号 | 分值 | 条件 |
|------|------|------|
| 标准问完全包含 | +0.45 | `question` 出现在 query（归一化后） |
| 主关键词 | +0.30 / 个 | 每个命中的 `keywords`（上限 0.60） |
| 同义词 | +0.20 / 个 | 每个命中的 `synonyms`（上限 0.40） |
| 类目标签 | +0.15 | query 含 `category` 或任一 `tags` |
| 优先级加成 | +0.02×(priority−3) | priority 1–5 |
| **单关键词封顶** | max **0.55** | 仅 1 个 keyword、无 synonym、未命中标准问 |

**术语匹配**：子串命中；排除「物质保修」对「质保」的交叉误命中。

## 3. 命中与空检索

- **命中**：`score ≥ retrieval_threshold`（默认 **0.7**）
- **排序**：score 降序 → priority 降序 → id 升序
- **返回**：Top `max_chunks`（默认 **3**）条
- **空检索**：无条目 ≥ 阈值 → 上报 CoAgent `empty_retrieval`，**不调用 Claude**（避免无依据幻觉）

## 4. 查询归一化

- 小写、去首尾空白
- 全角标点转半角
- 连续空白折叠

## 5. 运维约定

- FAQ 变更后更新 `index_meta.json` 的 `index_version` 与 `kb_last_sync`
- 索引滞后 >24h 且空检索率升高 → S2 场景根因链（对齐 OPS-203）
- 禁止在 `answer` 外编造政策；Claude 仅做基于片段的表述整理

## 6. 测试样例

| Query | 预期 |
|-------|------|
| `退货要几天` | 命中 `faq-return-001` |
| `发票怎么开` | 命中 `faq-invoice-001` |
| `暗物质保修期` | 空检索（「保修」为泛化词，单关键词封顶 <0.7） |
| `vip 积分翻倍吗` | 命中 `faq-member-001`（同义词/关键词） |
