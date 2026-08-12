# CoAgent 接手开发资源

## Knowledge

- [README：产品定位与演示场景](README.md)
  适合先理解 CoAgent 为什么存在、S1/S2/S3 分别代表什么，以及产品承诺的处置闭环。
- [开发、部署与测试文档](docs/dev-deploy-test.md)
  环境变量、API、目录和本地运行说明的主要入口；具体实现状态仍需与源码核对。
- [当前设计基线](docs/superpowers/specs/coagent-design-spec.md)
  适合追溯架构决策和验收标准，不应替代当前代码事实。
- [C4 Inline Observer](docs/architecture/c4-inline-observer.html)
  R1 真实 Demo Agent 接入后的 Context / Container / Component 视图。
- [R1 接入说明](docs/architecture/r1-inline-observer.md)
  `/v1/traces` 观察链路与本地验证步骤。
- [ADR-0001 OTel 契约](docs/adr/0001-otel-trajectory-contract.md)
  Trajectory 主交换格式决策。
- [FastAPI 入口](app/main.py)
  查看生命周期、路由挂载、管理台渲染和静态资源策略。
- [核心编排器](app/orchestrator.py)
  事件幂等、路由、诊断、评分、审计和降级路径的主干代码。
- [处置手册配置](data/ops_playbooks.json)
  三个场景的工具、提示词、评分规则与演示数据来源。
- [测试目录](tests/)
  判断当前行为契约最可信的资源，也是接手后修改代码的回归基线。
- [Git 历史](.git/)
  适合追踪近期架构变化及文档与实现不一致的原因。

## Wisdom (Communities)

- 当前项目维护者与实际使用方
  用于验证演示假设、真实 Agent 接入方式、审批边界和生产事故数据；这些信息无法仅从仓库得出。

## Gaps

- 仓库未记录实际部署拓扑、责任人、发布流程和生产密钥管理方式。
- 暂无真实工具适配器的接口规范；当前工具结果主要来自 playbook mock。
- `TODOS.md` 的 P0 状态已过期，不能作为剩余工作清单直接使用。
