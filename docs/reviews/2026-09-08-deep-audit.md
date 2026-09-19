# 项目深度审核与优化依据

审核日期：2026-09-08；代码基线：`4f9d87a58b8d5c905e5e716ae6e4bc80cf549520`，分支 `codex/interview-ready`。
本次交付为审核与计划，未实施以下代码修复。历史验证数字与本次检查分开记录。

## 结论

项目已具备全栈 LLM 应用的工程骨架：领域目录、Skill 路由、Provider、规则降级、服务端权益、会话存储、微信公众号和运营后台都有实现。面试叙事成立，但当前优势主要是应用集成与失败处理；对模型输出的强约束、基于来源的回答、多轮上下文、质量评测和部署后的行为验证仍有明显缺口。

优先顺序应调整为：修复可复现缺陷和 CI → 建立真实质量基线 → 接入有限的领域证据与多轮上下文 → 完成演示 → 通过公开部署门槛。保留 FastAPI、SQLModel、Next.js 和现有 SkillRegistry；不因技术栈展示而迁移到重型 Agent 框架或向量数据库。

## 审核方法与范围

- 阅读核心编排、Provider、Prompt、评测、会话、认证、URL 校验、trace、目录/播种、API 入口、聊天前端、Docker/Compose、CI/Release 和既有路线图。
- 用完全本地的 mock HTTP 响应检查 Provider 和 Skill；不发送真实模型请求。
- 运行评测、Provider、配置和文档测试，执行全量 Python lint/format 检查。
- 只读查询 GitHub CI 与 PR；未修改 GitHub 状态。
- 不是逐文件穷尽审查，也不是渗透测试或生产压测。未验证的风险明确标注为静态推断。
- 保留本地未跟踪 `apps/data/`。未查看真实环境文件内容。

## 当前验证证据

| 检查 | 本次结果 | 解释 |
|---|---|---|
| GitHub 最新提交 | 本地与远端均为 4f9d87a | 分支同步 |
| PR | [PR #1](https://github.com/Caser-86/gaokao-tianzhiyuan.agent/pull/1) 为 OPEN，目标 main | 已有 PR，无需重复创建 |
| CI | [运行 34061470567](https://github.com/Caser-86/gaokao-tianzhiyuan.agent/actions/runs/34061470567) failure | API Lint & Format 的 Ruff format check 失败 |
| 该 CI 其他 job | API Test、Web Lint、Web Test、Web Build、Docker Build success | PR workflow 检查临时合并树；镜像构建通过不等于运行验收通过 |
| 定向 pytest | 26 passed | test_eval_runner、test_llm_provider、test_config、test_documentation_consistency |
| 离线评测 | 13/13；路由/schema/fallback 100% | 固定 stub 的工程回归 |
| 全量 Ruff check | 通过 | 不是 format 结果 |
| 本地 Ruff format --check | 12 个文件需要格式化 | exit 1 |
| 本地 Black --check | 1 个文件需要格式化 | exit 1 |
| 上轮全量测试 | API 216、覆盖率 85%；Web 130 | 2026-09-07 历史记录，本轮未重跑完整套件 |

复现命令（在 `apps/api` 使用项目虚拟环境）：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_eval_runner.py tests/test_llm_provider.py tests/test_config.py tests/test_documentation_consistency.py
.\.venv\Scripts\python.exe -m app.evals.runner --format json
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m black --check .
```

## 发现清单

优先级：P0 = 首批处理的交付/正确性阻断，不代表安全漏洞评分；P1 = 面试核心体验或公开部署前应补；P2 = 有测量证据后推进。源码行号相对本次基线，后续可能变化。

| ID / 优先级 | 证据与触发条件 | 影响 | 建议 |
|---|---|---|---|
| A01 / P0 | CI 实际失败；`.github/workflows/ci.yml` lint job 直接安装未约束版本 ruff/black，本地 dev 版本有范围；同时使用两种 formatter | 本地 verify-project 成功不能证明 CI 绿色 | 统一版本与 formatter 策略；本地执行同一门禁；分离机械格式提交 |
| A02 / P0 | `apps/api/Dockerfile:17`—COPY 列表没有 skills；`config.py:29` 依赖仓库外层 skills 路径；wheel 只打包 app | 默认镜像没有正式 Prompt，配置 Provider 后仍可能走 Prompt 缺失降级 | 复制/打包 Prompt；容器内断言路径、hash 和实际 Provider stub 调用 |
| A03 / P0 | `docker-compose.yml` 未向 API 传入 GAOKAO_AGENT_SESSION_SECRET；`config.py:152` 拒绝生产默认 secret。本地 Settings(_env_file=None) 已复现拒绝启动 | 标准 Compose 切换 production 后，仅在宿主机设置变量不足以让容器接收它 | 显式传入生产 session secret；隔离临时卷做 production 启动验证 |
| A04 / P0 | `llm.py:100` 直接索引 choices 并链式 get；mock 200 响应 choices=[] → IndexError，顶层 []、message=null → AttributeError | Provider 协议错误逃离既有降级异常体系 | 校验响应信封，将畸形 JSON/空列表/null/错误类型归为 ProviderResponseFormatError |
| A05 / P0 | `skills.py:553` 只要 intent/summary 存在即原样接受；本地模拟 intent=invalid-intent、summary=42、actions=字符串均成功返回，无 debug_notes | 非法结构穿透后端，前端 actions.filter 等可能失败 | 用现有 Pydantic 强校验枚举、类型、长度、嵌套对象和动作目标 |
| A06 / P0 | `skills.py:589` fallback：仅“江苏985”即返回东南大学冲刺项和 confidence=0.81；本地复现 score=null、risk_flags=[] | 缺少个人信息却给出貌似量化建议；Prompt 限制没有覆盖规则路径 | 信息不足只给比较维度和最多三条追问；去除无依据的数值置信度与冲稳保判断 |
| A07 / P0（部署前） | Docker CMD 每次启动执行 seed_catalog；`seed_catalog.py:85` 已有学校也覆盖 summary/sections 等字段 | 静态推断：容器重启可能覆盖后台已编辑的目录内容 | 分离迁移、首次演示播种与服务启动；隔离 DB 复现“修改→重启→仍保留” |
| A08 / P1 | `runner.py:64` stub 忽略 messages；schema 检查只是 keys 子集；major-choice/volunteer-strategy 使用 request_failed；prompt-boundary 实际是域外路由 | 13/13 无法证明 Prompt 有效、抗注入或建议质量；破坏 Prompt 语义仍可能通过 | 分开协议回归、Prompt 组装契约、领域质量评测；真实模型手动运行并限定预算 |
| A09 / P1 | runtime resolver 使用 settings 配置，runner 固定解析空字符串；hash 只包含文件字节，不包括 skills.py 中附加 system 指令；Path(空字符串) 退成当前目录 | 上轮“统一”仅覆盖默认资产；自定义 Prompt 和实际发送消息身份仍可能不同 | 显式 --prompt；缺资产快速失败；同一 Prompt 快照生成消息及 effective hash；报告环境与数据版本 |
| A10 / P1 | `skills.py:474` 模型消息只有 system 和当前 user，目录查询是独立 Skill，未给模型注入目录证据 | 模型增强路径没有使用项目结构化数据来支持回答 | SQL 检索→来源包→LLM 解释；给 citation id，验证引用存在；无证据时降级 |
| A11 / P1 | `chat.py` 保存历史但不载入模型上下文；`chat-workspace.tsx:126` 只替换 response，history 仅初次读取 | 第二轮“那这个专业呢”无法稳定理解第一轮；当前轮对话展示不完整 | 限定最近 N 轮/字符预算；按主体取历史；前端追加消息并支持重新加载 |
| A12 / P1 | `tracing.py:18` 写 INFO；本地默认 logger INFO disabled；启动代码未见 app logger 配置；trace 在 save_exchange 前发出 | 静态推断：标准启动日志可能没有 trace；保存失败可能已记录为成功；无模型/token/成本记录 | 启动配置日志；完成持久化后记录最终结果；增加请求模型、返回模型、usage/耗时，缺失值为 null |
| A13 / P1（公开前） | 文本请求无 max_length；未发现应用/部署速率和并发预算；Provider 每次新建同步 Client，无输出 token 上限；匿名身份可新签发 | 流量与模型费用缺少硬上限，限单个匿名账号不足以防滥用 | 输入上限、IP/主体组合限流、全局并发与预算、总时限；有限重试只针对瞬时错误 |
| A14 / P1（公开前） | `routers/chat.py:1044` async 微信回调直接调用同步业务；`url_safety.py:49` 明确不解析 DNS | 静态风险：模型等待阻塞事件循环；普通域名解析到私网仍可能被请求。未开展并发/SSRF 攻击复现 | 先线程卸载与并发测试；外链获取限制来源或绑定验证后的连接地址，逐跳验证；按渠道再设计后台处理 |
| A15 / P2 | `main.py` 启动 create_all + DB 补列，与 Alembic 双路径；目录每次构建全量关系；后台文件很大 | 数据扩大、并发或 schema 演化时维护与延迟风险上升，尚无压测证据 | 生产以迁移为准；先量查询/锁等待再分页和批量；按功能渐进拆分 |
| A16 / P1 | 文档 consistency 测试仍只检查字符串 215/130/旧文件名；README 仍写 205；PROJECT_REVIEW 有旧 Prompt hash；offline-prompt.md 相对链接本地检查为不存在；报告 Prompt 表缺分隔行 | 面试证据易被追问击穿；上轮文档存在实际遗漏 | 单一 latest 验证索引、保留有日期历史；校验链接与图表渲染；修正兼容链接为 ../../../skills/... |

补充：`chat-workspace.tsx` 对模型动作目标仅检查非空字符串，直接作为 Link href 使用。不能据此断言已存在可利用 XSS；应把模型动作限制为服务端可解析的 school/major slug 或允许的内部路由，未知/外部协议直接拒绝（并入 A05）。

## 面试价值判断

可直接讲：SQL-first 的确定性查询、独立 Skill、服务端权益、Provider 降级、多渠道适配、会话隔离、数据来源声明。

当前需要准确表达：这是“有路由的领域 LLM 工作流”，没有发现模型自主规划、执行工具并反复观察结果的循环。可以展示自己的编排实现，无需为了名称引入多 Agent。

最能提升代表作质量的新增闭环：用户补充考生信息 → 从有限、带来源的数据查询证据 → 模型生成可引用的解释 → 契约检查 → 风险提示 → 可回放评测。这个闭环比再增加后台功能更接近 AI Agent / LLM 应用面试的核心问题。

## 未验证边界

- 本次没有重新构建或启动 Docker，容器问题来自构建文件和配置路径检查；GitHub Docker Build 已成功，但未做运行时验收。
- 未调用真实模型；实际回答质量、幻觉率、token 成本与路由模型版本无法确认。
- 未访问生产主机、GitHub Environment 配置、公开 HTTPS 或外部日志；不能确认已部署或实际生产风险发生。
- 未执行依赖漏洞数据库审计；不据版本号推断安全漏洞。
- A14 是源码边界分析，不是渗透测试结论。

后续任务、估算、依赖图与验收门见 [优化路线图](../superpowers/plans/2026-09-08-project-optimization-roadmap.md)。
