# Project Context

> 更新日期：2026-09-19。本文只描述当前代码和已验证事实；历史阶段的测试数字与决策记录见 `docs/verification/`、`PROJECT_REVIEW.md` 和 `PLAN.md`。

## 项目目标

高考填志愿.agent 是一个面向高考咨询场景的全栈 LLM 应用。它把学校、专业、榜单和内容运营数据放入结构化服务，由 Skill 路由和规则处理确定性问题，再按权限和预算调用 OpenAI-compatible 模型增强开放问题，同时提供 Web、微信公众号和运营后台入口。

它不是招生数据库，也不是新基础模型；根目录 `data/` 仅包含开发、测试和面试演示用的 demo 数据，不能直接用于真实志愿决策。

## 当前状态

- 面试展示版主链路已形成：目录查询、Agent 聊天、证据引用、受控多轮、规则降级、后台运营、微信公众号适配、离线评测和本地浏览器验收均已实现。
- 当前验证索引为 [`docs/verification/latest.json`](docs/verification/latest.json)：API 261 个用例、Web 132 个用例，Web typecheck/lint/build 和 Docker 镜像 CI 均已通过。
- T11 已加入消息长度、单进程模型并发、IP/主体窗口限流、全局日预算、请求总时限、有限重试和最终 trace；多 worker 共享预算尚未验证。
- 真实 Provider 的成对质量、token/cost 口径、Docker runtime、生产 HTTPS、监控、发布后 smoke、备份恢复和自动回滚仍未完成。

## 已完成功能

- SkillRegistry：目录查询 Skill 与高考咨询 Skill 的自动匹配、指定 Skill 调用和结构化输出。
- SQLModel/SQLite：学校、专业、关联、榜单来源、精选、会话、媒体事件、权益和公众号 replay receipt。
- LLM Provider：OpenAI-compatible Chat Completions，支持结构化 JSON、模型返回信息、超时和有限重试。
- 可靠性边界：模型不可用、配置错误、余额不足、非法响应和超时进入确定性降级，不直接把外部错误暴露为聊天 500。
- 证据链：服务端按明确实体筛选有限 SQL 证据，模型只能引用白名单 ID，来源元数据由服务端回填，前端显示证据卡片。
- 受控多轮：服务端按主体读取最近最多 6 轮、12000 字符的上下文，过滤客户端伪造历史和 system 消息。
- 渠道与运营：Next.js 公开站/聊天/后台、微信公众号明文与 AES 回调、内容审核、精选轮换、媒体分析事件和失败重试入口。
- 工程交付：Alembic、PowerShell smoke、Docker/Compose、Linux systemd/nginx 模板、pytest/Vitest、Ruff、TypeScript、GitHub Actions。

## 当前正在开发

当前没有已在代码中展开但未完成的功能分支。后续工作集中在公开部署前的验证和安全加固，统一记录在 [`TODO.md`](TODO.md)。

## 未完成任务

按优先级查看 [`TODO.md`](TODO.md)。关键公开前门槛是：真实 Provider 受控评测、多 worker 共享预算、出站请求进一步加固、账号/令牌生命周期、生产 Docker/HTTPS smoke、日志轮转和回滚演练。

## 当前技术栈

- 后端：Python 3.11+、FastAPI、Uvicorn、Pydantic Settings、SQLModel、SQLite、Alembic、HTTPX、PyAES。
- 前端：Next.js 15、React 19、TypeScript、Vitest、Testing Library、Tailwind CSS。
- LLM：OpenAI-compatible Chat Completions；Provider、模型名、Base URL 和 API Key 通过环境变量注入。
- 质量：pytest/pytest-cov、Ruff lint/format、Vitest、TypeScript typecheck、Next production build、数据资产校验和本地 HTTP smoke。
- 交付：Docker、Compose、GitHub Actions、PowerShell；Linux 模板包含 systemd 与 nginx。

## 核心架构

```text
Web / 微信公众号 / Admin
              |
       FastAPI routers
              |
 ConversationService
       |       |       \
 SkillRegistry  ACL    Session/Trace
   |       |
 Catalog  ZhangXueFeng Skill --> LLM Provider
   |
 SQLModel / SQLite
```

确定性目录查询优先走结构化数据；开放咨询才进入 LLM Skill。证据、权限、会话上下文、请求预算和 trace 均由服务端控制，模型不是唯一依赖。

## 关键目录

| 路径 | 用途 |
|---|---|
| `apps/api/app/` | API、路由、服务、模型、评测运行器 |
| `apps/api/tests/` | 后端接口、服务、迁移、安全和评测回归 |
| `apps/web/` | 公开页、聊天页、后台和前端测试 |
| `data/` | 唯一权威的 demo JSON 资产 |
| `skills/zhangxuefeng/` | 正式领域 Prompt/Skill 资产，运行时和离线评测共用 |
| `scripts/` | 数据校验、启动停止、smoke 和微信 AES 辅助脚本 |
| `deploy/` | Windows、systemd、nginx 和生产配置模板 |
| `docs/` | 文档、面试材料、运维手册、设计记录和验证证据 |

## 关键技术决策

1. 结构化学校/专业关系先使用 SQL，不为当前小规模 demo 数据引入向量数据库或重型 Agent 框架。
2. LLM 是增强层；目录能力和规则 fallback 在 Provider 不可用时仍可工作。
3. 客户端 metadata 不参与权益授权；服务端 session、数据库权益和环境模式才是授权事实。
4. Prompt 运行时和离线评测共用 `skills/zhangxuefeng/SKILL.md`，报告记录资产/effective hash，不记录 Prompt 原文。
5. 当前请求预算是进程内实现；多 worker 部署必须替换为共享存储后才可宣称全局限流/预算。
6. 演示数据必须携带 provenance 边界；未验证外部来源不能被包装成官方招生或排名事实。

## 已知问题

- guest session 不是完整账号系统，仍缺账号绑定、撤销和多设备管理。
- URL 安全已阻断常见本地/保留地址、凭据、危险重定向和超限文本，但 DNS rebinding、MIME/内容校验和出站速率限制仍待补齐。
- 请求预算、trace 和日志轮转仍依赖单进程/部署环境；外部日志删除、告警阈值和共享存储尚未实现。
- `data/` 是 demo 数据；真实数据接入还需要来源许可、更新责任、年份/地区校验和人工发布审核。
- 本地 Playwright 验收使用合成 Provider，不代表真实模型质量、token/cost 或招生准确率。

## 下一步

按 [`TODO.md`](TODO.md) 执行：先完成真实 Provider 受控评测和公开前安全/预算边界，再进行 Docker runtime、HTTPS、备份恢复、发布后 smoke、监控和回滚演练；只有真实非结构化数据证明 SQL-first 不足时，才重新评估检索升级。
