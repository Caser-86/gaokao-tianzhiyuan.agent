# 高考填志愿.agent

> 一个把结构化高考知识、可插拔 Skill 路由、OpenAI 兼容模型、确定性降级、权益控制和微信公众号接入串成完整业务闭环的全栈 AI Agent 应用。

[![CI](https://github.com/Caser-86/gaokao-tianzhiyuan.agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Caser-86/gaokao-tianzhiyuan.agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![React](https://img.shields.io/badge/React-19-149ECA?logo=react&logoColor=white)

![高考填志愿.agent 首页截图](docs/assets/home.png)

![高考填志愿.agent Agent 聊天页截图](docs/assets/chat.png)

![高考填志愿.agent 运营后台截图](docs/assets/admin.png)

> 以上为使用本地示例配置和合成管理员值生成的脱敏截图；没有真实模型密钥、用户数据或生产接口。完整截图素材保存在 [`docs/assets/`](docs/assets/)。

## 三分钟看懂项目

| 问题 | 回答 |
|---|---|
| 它解决什么问题？ | 为高考志愿咨询提供学校/专业查询、志愿问题分析、公众号回复和内容运营能力。 |
| 为什么是 Agent，而不只是聊天框？ | 自动路由接口会先做 Skill 匹配；当前 Web 聊天页则直接调用指定的高考咨询 Skill。两条路径都会执行权益判断、结构化输出与失败降级，并把媒体事件和失败原因留给运营后台。 |
| 核心 Agent 能力是什么？ | `SkillRegistry`、置信度路由、OpenAI-compatible Provider、结构化 JSON 输出、确定性 fallback、多渠道适配和轻量 Agent trace。 |
| 工程难点在哪里？ | 模型不稳定、用户权益、微信公众号 AES、多类型消息、内容审核、媒体失败重试和本地可复现交付。 |
| 如何证明不是概念 Demo？ | 仓库包含关系数据模型、运营后台、后端/前端测试、CI、Docker、冒烟脚本和部署模板；最新可追溯结果见 [`2026-08-30 验证记录`](docs/verification/2026-08-30-evaluation-and-data-trust.md)。 |
| 当前最重要的边界是什么？ | 演示数据不能用于真实志愿决策；生产发布、版本探针和回滚闭环仍需外部环境确认。 |

适合重点查看的三个入口：

1. [`apps/api/app/services/skills.py`](apps/api/app/services/skills.py)：Skill 注册、匹配和领域 Agent 实现。
2. [`apps/api/app/services/chat.py`](apps/api/app/services/chat.py)：聊天编排、权益决策和降级链路。
3. [`apps/web/components/admin/dashboard-shell.tsx`](apps/web/components/admin/dashboard-shell.tsx)：内容治理与 Agent 运营面。

## 项目定位

高考咨询不是一个适合“把所有数据塞进 Prompt”就结束的场景。学校、专业、榜单来源和内容版本需要结构化管理；模型调用需要成本与权益控制；回答错误和媒体处理失败需要被运营人员看见；微信公众号又有独立的签名、AES 和消息协议。

本项目因此采用“结构化数据为基础、LLM 作为增强、规则 fallback 保底、人工运营可介入”的设计：

- 基础学校与专业查询不依赖模型可用性。
- LLM 只在配置、权限和 Skill 条件满足时参与增强分析。
- 模型失败不会让聊天链路整体崩溃。
- 内容、榜单、精选轮换、权益和失败事件可在后台治理。
- 同一套 Agent 能力可服务 Web 和微信公众号渠道。

## 数据可信度边界

根目录 [`data/`](data/) 是用于开发、测试和面试演示的少量 JSON 资产，不是实时招生数据库。当前示例中的榜单链接和内容均不能作为官方录取依据；顶层 `data_provenance` 契约会被资产校验器检查，并由公开 API 返回、由学校/专业详情页展示。未来接入真实数据时，每条记录至少需要来源名称、来源 URL、发布日期/更新时间、适用年份、地区和“官方/二手资料”标记。发布前运行 `python scripts/verify-data-assets.py`，并在后台或页面展示数据更新时间与免责声明。详细规则见 [`data/README.md`](data/README.md)。

## 和直接询问 GPT/豆包有什么区别？

一句话：**底层模型可以相同，但本项目把模型放进了一个面向高考志愿的、可约束、可追踪、可运营的决策工作流。**它不是把一个通用聊天框换成高考主题，而是把模型变成领域系统中的增强组件。

| 维度 | 直接询问通用大模型 | 本项目 |
|---|---|---|
| 目标 | 泛化问答，依赖用户自己组织问题和判断结果 | 围绕高考志愿咨询，组织查询、分析、解释和后续行动 |
| 输入 | 一段自然语言；模型可能拥有联网、工具或记忆能力，但单次对话不保证具备本项目的领域上下文 | 考生可在问题中提供分数/位次、地区、年份、选科、偏好等业务上下文；请求同时携带渠道、Skill、会话和服务端主体/权益 |
| 知识与约束 | 由模型已有知识、临时检索或用户提供的材料决定 | 学校、专业、榜单来源和内容版本用结构化数据表达；确定性约束与 LLM 解释分开 |
| 结果 | 一次回答，用户需要自行复核来源、适用年份和风险 | 结构化结果、风险与行动建议；模型不可用时仍有规则化目录/降级路径 |
| 可靠性 | 重点是模型本身的回答能力 | 有服务端权益、输入安全边界、trace、离线评测、会话生命周期和失败原因 |
| 运营方式 | 通常停留在用户与模型的单次交互 | 有微信公众号适配、内容审核、媒体事件、人工重试和运营后台 |
| 工程交付 | 主要使用现成模型产品能力 | 完整的 FastAPI + Next.js + SQLModel、迁移、CI、Docker 和本地 smoke 链路 |

面试时应诚实地说：**这个项目没有训练一个新基础模型，也不能宣称替代 GPT/豆包；它展示的是如何把通用模型可靠地嵌入一个有结构化领域数据、业务规则、成本权限、隐私边界和运营反馈的 LLM 应用。**相关实现证据见 [`Skill 路由`](apps/api/app/services/skills.py)、[`聊天编排与降级`](apps/api/app/services/chat.py)、[`服务端权益`](apps/api/app/services/access_control.py)、[`Agent trace`](apps/api/app/services/tracing.py) 和 [`离线评测`](apps/api/app/evals/runner.py)。

## 系统架构

```mermaid
flowchart LR
    USER[Web 用户] --> WEB[Next.js Web]
    WECHAT[微信公众号] --> API[FastAPI API]
    OPS[运营人员] --> ADMIN[Next.js Admin]

    WEB --> API
    ADMIN --> API

    API --> CHAT[ConversationService]
    CHAT --> REGISTRY[SkillRegistry]
    REGISTRY --> CATALOG[Catalog Lookup Skill]
    REGISTRY --> DOMAIN[ZhangXueFeng Skill]
    DOMAIN --> LLM[OpenAI-compatible LLM]
    CHAT --> TRACE[Structured Agent Trace]
    CHAT --> SESSION[Session Store]

    API --> MEDIA[Media Analysis Provider]
    API --> ACL[Smart Analysis Access Control]
    API --> DB[(SQLModel / SQLite)]

    CATALOG --> DB
    MEDIA --> DB
    ACL --> DB
    SESSION --> DB
```

### Agent 请求链路

```mermaid
sequenceDiagram
    participant U as 用户/渠道
    participant A as FastAPI Adapter
    participant C as ConversationService
    participant S as SkillRegistry
    participant P as LLM Provider
    participant D as SQLModel

    U->>A: message + channel + user context
    A->>C: 归一化请求
    C->>D: 读取服务端模式与用户权益
    alt /messages 或渠道适配器
        C->>S: 按置信度匹配 Skill
    else 当前 Web /skills/{skill_id}/invoke
        C->>S: 获取指定 Skill（zhangxuefeng）
    end
    alt 结构化目录问题
        S->>D: 查询学校/专业/榜单
        D-->>S: 结构化领域数据
    else LLM 增强问题
        S->>P: JSON 协议调用
        alt Provider 成功
            P-->>S: 结构化分析结果
        else 配置/网络/余额/格式错误
            S-->>C: 确定性降级结果
        end
    else 置信度不足
        S-->>C: 澄清问题
    end
    C->>D: 以服务端解析的主体 + session_id 校验并保存会话消息
    C->>TRACE: candidates + selection + provider + latency + fallback reason
    C-->>A: summary + analysis + risks + actions
    A-->>U: Web JSON 或微信 XML/AES XML
```

## 核心能力

| 能力 | 当前实现 | 关键位置 |
|---|---|---|
| Skill 路由 | 内置目录查询与高考咨询 Skill，按置信度选择 | [`skills.py`](apps/api/app/services/skills.py) |
| LLM Provider | OpenAI-compatible Chat Completions，支持 `/v1`、`/v3` 和 Agent Plan 版本路径，结构化 JSON 输出 | [`llm.py`](apps/api/app/services/llm.py) |
| 失败降级 | 区分未配置、请求失败、余额不足和非法响应 | [`chat.py`](apps/api/app/services/chat.py) |
| Agent trace | 记录候选/选择 Skill、版本、Prompt SHA-256 指纹、Provider、模型调用标记、耗时和降级原因；session 只保留摘要引用 | [`tracing.py`](apps/api/app/services/tracing.py) |
| 会话持久化 | SQLModel 保存用户/Agent 消息，30 天滚动保留，按用户读取和删除；不自动注入长期记忆 | [`chat_sessions.py`](apps/api/app/services/chat_sessions.py) |
| 离线评测 | 13 个固定样本覆盖路由、信息缺失、敏感请求边界、结构化输出、Provider 失败与 fallback；报告不访问真实模型 | [`runner.py`](apps/api/app/evals/runner.py) |
| 领域知识 | 学校、专业、关联、榜单来源、精选和搜索入口关系模型 | [`models/catalog.py`](apps/api/app/models/catalog.py) |
| 智能分析权益 | `off / gated / on` 与用户 `smart_analysis` 权益；策略只由服务端模式和数据库权益决定 | [`access_control.py`](apps/api/app/services/access_control.py) |
| 微信公众号 | URL 验证、明文/AES、文本/图片/语音/位置/链接和菜单事件 | [`routers/chat.py`](apps/api/app/routers/chat.py) |
| 媒体分析 | 图片 Provider、字段提取、审计记录、失败原因和重试入口 | [`media_analysis.py`](apps/api/app/services/media_analysis.py) |
| 内容运营 | 审核、精选轮换、榜单、摘要、正文、关联内容和图片建议 | [`routers/admin.py`](apps/api/app/routers/admin.py) |
| 数据来源边界 | `data_provenance` 契约、资产校验、公开 API 字段和详情页声明 | [`data_provenance.py`](apps/api/app/services/data_provenance.py)、[`data-provenance-notice.tsx`](apps/web/components/public/data-provenance-notice.tsx) |
| 前端产品面 | 公开目录、Agent 聊天、权益入口和运营后台 | [`apps/web/app`](apps/web/app) |
| 工程交付 | 测试、CI、Docker、PowerShell、systemd/nginx 和运维手册 | [`.github/workflows`](.github/workflows) |

## 值得在面试中展开的设计

### 1. 为什么没有直接引入向量数据库？

当前核心知识是学校、专业、榜单来源和关联关系，结构化 SQL 查询更确定、更容易测试，也没有额外服务成本。6 个固定样本的 SQL 覆盖 spike 得到 `33.33%` 覆盖率、`100%` 标签一致率，未发现立即引入向量检索的证据；项目保留 LLM Skill 处理开放问题，后续先扩充真实非结构化样本再重评估。详见 [`SQL Coverage Spike`](docs/verification/2026-08-25-phase3.7-retrieval-spike.md)。

### 2. 如何面对 LLM 的非确定性？

- 模型输出要求 JSON object，并在服务边界解析。
- Provider 配置、请求、余额和格式错误使用不同失败原因。
- Skill 在模型不可用时返回规则化结果，而不是直接抛给用户 500。
- 当前已接入轻量调用 trace：不记录完整消息、Prompt、API Key 或用户标识原值；会话消息单独按 30 天滚动策略持久化；固定离线评测集已覆盖路由、结构化输出和 Provider fallback，内部 trace/report 记录 Skill 版本与 Prompt SHA-256 指纹。

### 3. 为什么需要权益控制和运营后台？

LLM 调用具有真实成本，且高考建议需要内容治理与人工解释。项目把模型增强能力放在 `off / gated / on` 策略后，并为内容审核、媒体失败、榜单来源和精选排期提供后台入口，形成“Agent 能力—商业权限—人工运营”的闭环。

### 4. 多渠道如何复用同一套能力？

Web、通用微信渠道和微信公众号只负责协议适配，核心请求统一进入 `ConversationService`。公众号层额外处理签名、AES、XML 和事件映射，避免把渠道细节泄漏进 Skill 实现。

## 三分钟面试 Demo

建议按下面顺序演示，而不是逐页介绍所有功能：

1. 打开 `/`，说明结构化学校/专业内容不依赖 LLM，并在详情页指出当前是演示数据而非权威招生数据。
2. 从首页快捷问题进入 `/chat`，说明当前 Web 主界面直接调用 `zhangxuefeng` Skill。
3. 通过 `/api/chat/messages` 演示自动 Skill 匹配，再询问“某省某分数如何定位”，对比自动路由与直接调用两条入口。
4. 临时不配置 LLM 或使用测试故障场景，展示聊天仍返回规则降级结果。
5. 打开 `/admin`，展示智能分析模式、用户权益、内容审核和媒体失败记录。
6. 最后展示 API trace 设计与测试，说明可以解释 Skill 选择、模型调用和降级原因，再展示 CI 与测试目录。

可直接使用的录制台词和逐题问答见 [`三分钟 Demo 脚本`](docs/interview/three-minute-demo.md) 与 [`面试问答包`](docs/interview/interview-qa.md)。仓库还提供一个使用本地示例数据和合成配置生成的 [`脱敏交互视频候选`](docs/assets/gaokao-agent-demo.webm) 及其 [`旁挂 WebVTT 字幕`](docs/assets/gaokao-agent-demo.vtt)；浏览器播放和后台样式已人工抽查通过，但候选仍是静音录屏，旁白可按面试需要补录，不代表生产演示或最终面试版。

本地默认入口：

| 页面 | 地址 |
|---|---|
| 公开首页 | `http://127.0.0.1:3000` |
| Agent 聊天 | `http://127.0.0.1:3000/chat` |
| 运营后台 | `http://127.0.0.1:3000/admin` |
| API 健康检查 | `http://127.0.0.1:8000/health` |
| API 版本探针 | `http://127.0.0.1:8000/version` |
| Chat 健康检查 | `http://127.0.0.1:8000/api/chat/health` |

## 快速启动

### 方式一：Windows 本地脚本

准备 API 与 Web 环境变量后，在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1
```

停止服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1
```

### 方式二：Docker Compose

```powershell
Copy-Item .env.docker.example .env
```

将 `.env` 中的 `GAOKAO_AGENT_ADMIN_TOKEN` 替换为仅供本地使用的非默认值，然后运行：

```powershell
docker compose up --build
```

`NEXT_PUBLIC_GAOKAO_AGENT_API_URL` 是浏览器可访问的 API 根地址，Compose 构建时必填；本地可使用示例中的 `http://localhost:8000`，生产环境必须改成浏览器能访问的 HTTPS/API 根地址，代码会自动追加 `/api/...` 路径。

### 方式三：分别启动 API 和 Web

API：

```powershell
Set-Location apps/api
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --port 8000
```

Web：

```powershell
Set-Location apps/web
Copy-Item .env.example .env.local
npm install
npm run dev
```

## 配置

### API

示例文件：[`apps/api/.env.example`](apps/api/.env.example)

```env
GAOKAO_AGENT_ENVIRONMENT=development
GAOKAO_AGENT_RELEASE_VERSION=dev
GAOKAO_AGENT_ADMIN_TOKEN=replace-with-a-local-token
GAOKAO_AGENT_SESSION_SECRET=replace-with-a-local-session-secret
GAOKAO_AGENT_DATABASE_URL=sqlite:///./gaokao-agent.db
GAOKAO_AGENT_WECHAT_SIGNATURE_TTL_SECONDS=300
GAOKAO_AGENT_WECHAT_MAX_BODY_BYTES=262144
GAOKAO_AGENT_CHAT_SESSION_RETENTION_DAYS=30
GAOKAO_AGENT_MEDIA_ANALYSIS_RETENTION_DAYS=30
GAOKAO_AGENT_AGENT_TRACE_RETENTION_DAYS=7

GAOKAO_AGENT_LLM_PROVIDER=openai_compatible
GAOKAO_AGENT_LLM_BASE_URL=https://your-provider.example
GAOKAO_AGENT_LLM_API_KEY=replace-with-your-api-key
GAOKAO_AGENT_LLM_MODEL=replace-with-your-model
GAOKAO_AGENT_SMART_ANALYSIS_MODE=off

GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=
```

`GAOKAO_AGENT_LLM_BASE_URL` 填 Provider 的 API Base URL。服务端会根据 Base URL 末尾的版本路径拼接 `/chat/completions`；例如火山方舟 Agent Plan 使用 `https://ark.cn-beijing.volces.com/api/plan/v3`，普通未带版本路径的 Provider 才会追加 `/v1/chat/completions`。

智能分析模式：

- `off`：完全关闭模型增强，只返回目录或规则结果。
- `gated`：仅拥有 `smart_analysis` 权益的用户可调用模型增强。
- `on`：所有用户均可调用模型增强。

Web 聊天会使用 API 签发的 HTTP-only `gaokao_session` Cookie；生产环境必须设置非默认的 `GAOKAO_AGENT_SESSION_SECRET`。公众号回调默认只接受 300 秒内的 timestamp，且 body 上限为 256 KiB。会话和媒体分析事件默认保留 30 天，Agent trace 默认按 7 天日志轮转约定处理；API 启动和写/查询路径会清理过期 SQLite 记录。登录用户可调用 `DELETE /api/privacy/me` 删除自己的会话、消息和媒体分析事件。开发/测试环境仍保留带 `user_id` 的兼容调用，不能作为生产身份方案。

### Web

示例文件：[`apps/web/.env.example`](apps/web/.env.example)

```env
GAOKAO_AGENT_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_GAOKAO_AGENT_API_URL=http://127.0.0.1:8000
GAOKAO_AGENT_ADMIN_TOKEN=replace-with-the-same-local-token
```

Web 和 API 的管理员 token 必须一致。生产环境禁止使用 `dev-admin-token`。

## 外部 Skill 与模型

项目可选加载本地张雪峰风格 Skill：

```powershell
git clone https://github.com/alchaincyf/zhangxuefeng-skill.git vendor/zhangxuefeng-skill
```

默认查找位置：

- `skills/zhangxuefeng/SKILL.md`（项目内置的最小可运行提示词）
- `vendor/zhangxuefeng-skill/SKILL.md`
- `.tmp/zhangxuefeng-skill/SKILL.md`

外部 Skill 路径存在时可以覆盖项目内置版本。仓库内置提示词只负责高考志愿分析的安全边界和结构化输出，不包含实时录取数据。

如果没有配置 LLM Provider，Agent 仍可运行目录 Skill 和规则降级链路。仓库不会包含你的模型密钥。

## 微信公众号

回调端点：

- `GET /api/chat/channels/wechat/official-account`
- `POST /api/chat/channels/wechat/official-account`

需要在 API 本地 `.env` 中配置公众号 token、App ID 和 43 字符 EncodingAESKey。不要将这些值提交到 Git。

AES 辅助脚本：

```powershell
python scripts/wechat_aes_helper.py decrypt `
  --value "<Encrypt payload>" `
  --app-id "<wechat app id>" `
  --encoding-aes-key "<43-char aes key>"
```

## 测试与验证

源码静态统计：

- 后端：26 个测试模块，另有 1 个 `conftest.py`；静态统计 194 个测试函数，pytest 当前收集 205 个用例（含参数化展开）。
- 前端：28 个测试模块，另有 1 个 `setup.ts`；静态统计 129 个 `test/it` 用例。
- CI：API lint/test、迁移冒烟、Web lint/test/build、API/Web Docker 构建；trace、会话、离线评测、检索边界和可信身份回归测试位于 `test_chat_services.py`、`test_chat_sessions.py`、`test_eval_runner.py`、`test_retrieval_spike.py` 和 `test_auth_context.py`。

本节不把历史运行结果当作当前事实。可使用以下命令生成当前机器和当前 commit 的验证结果：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
```

分开验证：

```powershell
Set-Location apps/api
python -m pytest -q
python -m app.evals.runner --format markdown

Set-Location ../..
python scripts/verify-data-assets.py
python scripts/tests/test_verify_data_assets.py

Set-Location apps/web
npm run test:coverage
npm run typecheck
npm run lint
npm run build
npm audit --audit-level=moderate
```

2026-08-25 本地验证记录（基线 HEAD `772948a6f6fe28b353007b009658e277f07475ed`，工作树未提交）已执行：API `205 passed`、后端总覆盖率 `85%`、Web `129 passed`、Web 语句/分支/函数覆盖率 `86.64% / 84.21% / 72.34%`、Web typecheck 和生产构建通过；会话与微信幂等迁移经过 upgrade/downgrade/upgrade 往返验证；离线评测 9/9 样本通过；SQL 覆盖 spike 为 6/6 标签一致；客户端权益伪造、可信身份、平台权益主体、公众号重放、URL/媒体输入安全、隐私删除、后台 Action 失败反馈、并发加载和 `/version` 版本探针回归通过；隔离本地栈的完整 HTTP smoke（含公众号明文/AES 多类型回调和 `dev` 版本断言）通过，随后在同一持久化 SQLite 上完成 `release-old → release-new → release-old` 三段版本 smoke/回滚演练；首页/聊天/后台脱敏截图已生成；三分钟 Demo 脚本和面试问答包的文档链接、敏感模式与 diff 检查通过。详细结果见 [`docs/verification/2026-08-25-phase2-verification.md`](docs/verification/2026-08-25-phase2-verification.md)、[`docs/verification/2026-08-25-phase3.1-verification.md`](docs/verification/2026-08-25-phase3.1-verification.md)、[`docs/verification/2026-08-25-phase3.2-verification.md`](docs/verification/2026-08-25-phase3.2-verification.md)、[`docs/verification/2026-08-25-phase3.3-3.5-evaluation.md`](docs/verification/2026-08-25-phase3.3-3.5-evaluation.md)、[`docs/verification/2026-08-25-phase3.6-3.7-verification.md`](docs/verification/2026-08-25-phase3.6-3.7-verification.md)、[`docs/verification/2026-08-25-phase4.1-verification.md`](docs/verification/2026-08-25-phase4.1-verification.md)、[`docs/verification/2026-08-25-phase4.2-verification.md`](docs/verification/2026-08-25-phase4.2-verification.md)、[`docs/verification/2026-08-25-phase4.3-verification.md`](docs/verification/2026-08-25-phase4.3-verification.md)、[`docs/verification/2026-08-25-phase4.4-verification.md`](docs/verification/2026-08-25-phase4.4-verification.md)、[`docs/verification/2026-08-25-phase4.5-verification.md`](docs/verification/2026-08-25-phase4.5-verification.md)、[`docs/verification/2026-08-25-phase4.6-verification.md`](docs/verification/2026-08-25-phase4.6-verification.md)、[`docs/verification/2026-08-25-phase4.7-4.9-verification.md`](docs/verification/2026-08-25-phase4.7-4.9-verification.md)、[`docs/verification/2026-08-25-phase5.5-5.6-verification.md`](docs/verification/2026-08-25-phase5.5-5.6-verification.md) 和 [`docs/verification/2026-08-25-phase5.7-5.8-verification.md`](docs/verification/2026-08-25-phase5.7-5.8-verification.md)。

2026-08-30 本轮验证基线（工作树基于 `f5a8340`）：API `213 passed`、Web `129 passed`、离线评测 13/13 通过、数据资产结构校验通过。详细命令、Prompt 一致性和数据可信度边界见 [`evaluation-and-data-trust verification`](docs/verification/2026-08-30-evaluation-and-data-trust.md)；本轮仍未声称完成生产部署、公开 HTTPS smoke、监控告警或外部回滚演练。

2026-08-31 数据来源契约验证（基于 `ce72eb5` 工作树）：API `215 passed`、Web `130 passed`、数据资产结构与来源契约校验通过、Web typecheck/lint 通过。公开搜索/列表/详情 API 返回 `data_provenance`，学校和专业详情页展示演示数据、更新时间、来源范围和免责声明。完整命令与边界见 [`data provenance contract verification`](docs/verification/2026-08-31-data-provenance-contract.md)；生产权威数据接入、刷新责任和 HTTPS smoke 仍需外部确认。

## 目录结构

```text
apps/
  api/                         FastAPI、SQLModel、Skill、Provider 与测试
  web/                         Next.js 公开站、聊天、后台与测试
data/                          被跟踪的 JSON 演示内容资产
deploy/
  linux/                       systemd、nginx 与环境变量模板
  windows/                     Windows 运行模板
docs/
  assets/                      README 截图与脱敏 Demo 视频候选
  interview/                   三分钟 Demo 脚本与面试问答包
  operations/                  运维交接手册
  superpowers/                 设计规格与实施计划
scripts/                       启停、验证、冒烟与微信 AES 工具
.github/workflows/             CI 与 Release workflow
PROJECT_REVIEW.md              代码证据、亮点、风险与成熟度评审
PLAN.md                        从 MVP 到面试代表作的分阶段路线图
```

## 部署资料

- [Docker Compose](docker-compose.yml)
- [Windows 运行模板](deploy/windows/README.md)
- [Linux systemd + nginx 模板](deploy/linux/README.md)
- [本地交接与排障手册](docs/operations/local-handover-runbook.md)
- [生产就绪矩阵](docs/operations/production-readiness-matrix.md)
- [SQLite 备份与恢复手册](docs/operations/backup-restore-runbook.md)
- [Release smoke 与回滚手册](docs/operations/release-smoke-rollback-runbook.md)

当前仓库具备镜像发布与手工部署模板；工作树已收紧 Release 门禁与生产 Web API 地址策略，但还没有完成生产环境审批、HTTPS、自动迁移、发布后 smoke、监控告警和自动回滚闭环。详细边界见 [`PROJECT_REVIEW.md`](PROJECT_REVIEW.md)。

## 项目状态与路线图

第一阶段的文档和展示增强已完成；当前工作树已执行 Phase 2.1—2.8、Phase 3.1—3.7、Phase 4.1—4.9、Phase 5.1—5.4、Phase 5.6、Phase 5.8，并完成 Phase 5.5 的本地 smoke/版本断言、重复 smoke 回归和同库 old→new→old 回滚演练，以及 Phase 5.7 的 Demo 脚本/录制清单和本地脱敏视频候选：修复本地冒烟脚本、建立验证记录、收紧 Release/生产 API 配置、增加 JSON 资产校验、统一运行时文档、补齐现有 smoke 证据，接入不含敏感原文的 Agent trace，加入 30 天滚动会话持久化与页面恢复，建立 13 个固定样本的离线评测基线，记录 Skill 版本与 Prompt 指纹，完成 SQL 覆盖边界 spike，阻断客户端 metadata 伪造智能分析权益，建立服务端签发的 HMAC guest session 与 Web cookie 身份边界，让平台权益查询复用服务端主体，为公众号回调增加 timestamp 窗口、body 上限和 MsgId/nonce 幂等，为图片/官网 URL 增加协议、主机、重定向和响应体边界，为会话/媒体事件/trace 建立保留、清理和用户删除规则，并为后台写操作加入结构化失败反馈、独立请求并发加载和首批内容质量组件拆分。`verify-project.ps1`、API/Web 测试、覆盖率、typecheck、Web 生产构建和隔离本地栈 HTTP smoke/版本断言已在 2026-08-25 本地通过；GitHub tag Release、Docker 实际发布、生产 post-deploy smoke 和 rollback 尚未完成。根目录 `data/` 是唯一权威源，未跟踪的 `apps/data/` 仅保留在当前本地工作区，CI 会拒绝其进入仓库。2026-08-30 的最新评测与数据边界证据见 [`evaluation-and-data-trust verification`](docs/verification/2026-08-30-evaluation-and-data-trust.md)。后续优先级为：

1. 完成生产发布后 smoke、回滚演练和外部部署确认（Phase 5.5）。
2. 按评测证据扩充非结构化问题样本，达到量化阈值后再评估混合检索。
3. 按 [`三分钟 Demo 脚本`](docs/interview/three-minute-demo.md) 为已复核的静音 [`脱敏 Demo 视频候选`](docs/assets/gaokao-agent-demo.webm) 视面试场景补录旁白；旁挂字幕已提供，问答包已在 Phase 5.8 补齐。

完整任务表、依赖关系和验收标准见 [`PLAN.md`](PLAN.md)。

## 安全与数据声明

- 不要提交 `.env`、`.env.local`、API Key、管理员 token、微信 token、App ID、AES Key、数据库或真实用户数据。
- 当前目录数据是用于功能演示的少量样例，其中可能包含占位来源；不能用于真实招生、排名或志愿决策。会话消息默认保留 30 天；聊天与会话主体已由服务端 guest session 解析，开发/测试环境仍保留显式 `user_id` 兼容回退，不能视为账号级认证。
- 高考政策、招生计划和录取数据具有年份与地区差异，生产使用前必须接入可追溯权威来源。
- 当前账号注册/撤销、DNS rebinding、速率限制、媒体 MIME/内容校验和外部日志轮转自动化仍有待加固；Phase 4.5 已阻断常见协议、凭据、本地/保留地址、危险重定向和超限 HTML 路径，Phase 4.6 已明确会话/媒体/trace 的保留与用户删除边界，客户端 metadata 扩权问题已在 Phase 4.1 阻断，聊天与平台权益身份上下文已在 Phase 4.2—4.3 收紧，公众号重放已在 Phase 4.4 增加基础防护，详见项目评审。

## 深入阅读

- [`PROJECT_REVIEW.md`](PROJECT_REVIEW.md)：完整仓库评审、架构证据、亮点、缺口与面试建议。
- [`PLAN.md`](PLAN.md)：分阶段实施计划、优先级、依赖和 Definition of Done。
- [`docs/operations/local-handover-runbook.md`](docs/operations/local-handover-runbook.md)：本地运行、冒烟和排障。
- [`docs/interview/three-minute-demo.md`](docs/interview/three-minute-demo.md)：录制时间线、台词和安全清单。
- [`docs/interview/interview-qa.md`](docs/interview/interview-qa.md)：架构、Agent、评测、安全、成本和生产差距问答。
- [`docs/verification/2026-08-30-evaluation-and-data-trust.md`](docs/verification/2026-08-30-evaluation-and-data-trust.md)：本轮 Prompt、评测、数据治理和本地验证记录。

---

**简历一句话：** 基于 FastAPI、Next.js、SQLModel 和 OpenAI-compatible Provider 构建高考志愿 AI Agent，完成 Skill 路由、结构化模型输出、失败降级、用户权益、微信公众号 AES、多模态事件审计、内容运营后台及 CI/CD 交付骨架。
