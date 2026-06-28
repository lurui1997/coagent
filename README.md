<div align="center">

# CoAgent

### AI Agent 事故指挥官

**Agent 上线之后，运行失败、质量异常、成本失控——CoAgent 帮你在出事那一刻，快速看懂、敢拍板、留得住痕。**

![赛道](https://img.shields.io/badge/赛道-ToB%20AI%20Agent-2563eb)
![定位](https://img.shields.io/badge/定位-Agent%20运行态%20Ops-7c3aed)
![License](https://img.shields.io/badge/License-MIT-64748b)

🌐 [官网](http://www.aikipedia.cn/coagent/) · 🏗 [架构图](docs/diagrams/coagent-architecture.html) · 📘 [开发文档](docs/dev-deploy-test.md)

<br />

<video src="docs/demos/coagent-demo-15s-2026-06-28T04-35-20.webm" autoplay loop muted playsinline controls width="100%"></video>

*事件接入 → 场景路由 → 处置手册+工具 → 根因推理 → 把握度评分 → 分级处置 · 审计留痕*

</div>

---

## 为什么需要 CoAgent

**Agent 做 demo 都挺好，一上线就翻车——而出事那一刻，没人敢拍板。**

企业 Agent 试验已很普遍，但真正跑在生产里的系统，往往卡在「出事时怎么办」：排查慢、靠老师傅、不留痕、不敢动。CoAgent 聚焦 **Agent 上线之后的运行态运维**，把**处置决策**做成产品，而不是又一套告警面板。

| 典型事故 | 你现在的困境 | CoAgent 帮你 |
|---|---|---|
| 客服 Agent 被限流，失败率飙升 | 跨系统查日志，只能等原工程师 | 给出根因假设、影响判断和可执行建议 |
| RAG Agent 空检索仍胡答 | 指标看起来正常，盲目重试更糟 | 识别质量异常，明确「不能盲动」 |
| 内容 Agent Token 超预算 | 只知道超支，不知限流还是暂停 | 风险分级，高风险动作必须升级 |

**适合谁用：** Agent 交付团队、企业 AI 平台与 SRE、接手第三方 Agent 的客户 IT——也就是**出岔子时得拍板「动还是不动」的那个人**。

---

## CoAgent 做什么

一条流水线，覆盖从发现到复盘：

| 阶段 | 回答的问题 |
|---|---|
| **发现** | 发生了什么？ |
| **诊断** | 为什么发生？证据在哪？ |
| **决策** | 要不要动？把握有多大？ |
| **处置** | 应该怎么动？谁有权批准？ |
| **验证** | 处置有效吗？ |
| **沉淀** | 谁做了什么？下次怎么更快？ |

> 当前版本提供**处置建议、人工审批与模拟验证**，不声称自动修复生产系统。

---

## 三个核心设计

**① 可解释的把握度评分**

不依赖模型自报「我很确定」，而是用数据完整度、手册匹配度、推理一致性三个维度给出 0–100 分和 🟢🟡🔴 分级——让值班人几秒内决定动不动，也敢追问依据。

**② 风险分级 = 处置权限**

| 分级 | 含义 | 你能做什么 |
|---|---|---|
| 🟢 可执行 | 证据充分 | 可直接处置（如重试） |
| 🟡 需确认 | 有不确定性 | 人工确认后再动 |
| 🔴 升级 | 风险高 / 证据弱 | 必须升级负责人 |

**③ 管理台闭环 + 持续校准**

诊断、评分、处置建议与审计时间线集中在管理台完成；每次人工反馈回流，持续完善处置手册与规则。IM 协同（飞书卡片）在路线图中，当前以管理台为主。

---

## 演示场景

三个场景共用同一条流水线，展示 **敢动手 → 不敢盲动 → 必须升级** 的处置边界递进：

| 场景 | 事故类型 | 典型因果 | 决策 |
|---|---|---|---|
| **S1** 客服限流 | 运行失败 | 并发上升 → API 429 → 服务不可用 | 🟢 可重试 |
| **S2** RAG 空检索 | 质量异常 | 索引延迟 → 空检索 → 错误回答 | 🟡 需确认，禁止盲重试 |
| **S3** 成本超预算 | 成本失控 | 流量/模板变化 → Token 激增 → 超日预算 | 🔴 升级负责人 |

---

## 快速体验

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --reload --port 8000
```

打开 http://localhost:8000/ → **处置工作台** 触发 S1 / S2 / S3，观察评分分级与审计时间线。

可选：用 `agents/` 下的三个示例 Agent（客服 / 检索 / 内容）模拟真实上报，详见 [开发文档 · Agent 接入](docs/dev-deploy-test.md)。

---

## 延伸阅读

| 资料 | 内容 |
|---|---|
| [架构图](docs/diagrams/coagent-architecture.html) | 技术架构与业务流程，统一处置流水线自动循环演示 |
| [开发 · 部署 · 测试](docs/dev-deploy-test.md) | 环境变量、API、项目结构、测试与部署 |
| [官网](http://www.aikipedia.cn/coagent/) | 产品叙事与路线图 |

---

## License

[MIT](LICENSE)

---

<div align="center">
<sub>CoAgent · 2026 黑客松项目（微软孵化器 × 小宿科技 · ToB AI Agent 赛道）</sub>
</div>
