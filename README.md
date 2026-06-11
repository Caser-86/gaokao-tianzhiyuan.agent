# 高考填志愿.agent

一个面向高考志愿咨询场景的智能问答与内容运营系统。项目以 FastAPI 作为后端服务，Next.js 作为前端界面，支持学校/专业/志愿填报问答、张雪峰风格技能接入、OpenAI 兼容大模型调用、微信公众号回调、智能分析权益控制和运营后台管理。

## 项目定位

本项目适合用作：

- 高考志愿咨询产品 MVP
- 公众号高考问答机器人后端
- LLM + 垂直领域 Skill 的集成样例
- 内容运营后台与智能分析权限控制样例
- Windows 本地可运行的全栈项目模板

## 核心功能

- 公共内容展示：学校、专业、精选内容、榜单参考等公开页面。
- 高考问答入口：Web `/chat` 页面可直接调用后端问答网关。
- 技能路由：内置 `zhangxuefeng` 技能路由，可识别学校、专业、分数定位、志愿建议等问题。
- 大模型接入：支持 `openai_compatible` Provider，可接入 OpenAI 兼容接口、中转接口或 MiMo 等兼容服务。
- 稳定兜底：当模型配置缺失、接口异常、余额不足或返回非标准 JSON 时，系统会返回规则化兜底结果，不会让聊天链路崩溃。
- 智能分析开关：支持全局关闭、全局开启、按用户权益开放三种模式。
- 用户权益控制：可按用户维护 `smart_analysis` 权益，决定是否允许调用模型增强分析。
- 管理后台：提供内容管理、精选内容、榜单参考、关联内容、智能分析设置、媒体分析记录等运营能力。
- 微信公众号回调：支持公众号 URL 验证、文本消息、关注/取消关注、菜单事件、图片/语音/位置/链接等基础消息处理。
- 微信 AES：支持公众号安全模式下的 AES 加解密、签名验证和本地辅助脚本。
- 媒体分析预留：图片/视频分析接口已预留 Provider 配置和后台记录能力，方便后续接入视觉模型。
- 本地一键启动：提供 Windows PowerShell 启动脚本、停止脚本、冒烟测试脚本和完整验证脚本。

## 技术栈

- 后端：Python、FastAPI、SQLModel、SQLite、HTTPX、Pytest
- 前端：Next.js 15、React、TypeScript、Vitest、Testing Library
- 大模型：OpenAI 兼容 Chat Completions 接口
- 微信：微信公众号被动回复、签名校验、AES 安全模式
- 工程化：PowerShell scripts、Next production build、API/Web 自动化测试

## 目录结构

```text
apps/
  api/                       FastAPI 后端服务
  web/                       Next.js 前端应用
data/                        本地 SQLite 数据目录
deploy/
  linux/                     Linux systemd + nginx 部署模板
  windows/                   Windows 运行模板
docs/
  operations/                运维交接文档
  superpowers/               历史设计与实施计划文档
scripts/
  start-local-stack.ps1      本地启动 API + Web
  stop-local-stack.ps1       停止本地服务
  smoke-local-stack.ps1      本地冒烟测试
  verify-project.ps1         项目完整验证
  wechat_aes_helper.py       微信 AES 调试辅助工具
vendor/                      本地外部技能目录，默认不提交
```

## 快速启动

### 方式一：一键启动推荐

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -RunSmoke
```

脚本会启动：

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:3000`
- Admin: `http://127.0.0.1:3000/admin`
- Chat: `http://127.0.0.1:3000/chat`

日志会写入 `.tmp/`。

停止本地服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1
```

### 方式二：手动启动 API

```powershell
cd apps/api
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/chat/health
```

### 方式三：手动启动 Web

```powershell
cd apps/web
Copy-Item .env.example .env.local
npm install
npm run dev
```

## 环境变量

### API 配置

API 环境变量示例文件：

- [apps/api/.env.example](apps/api/.env.example)

常用配置：

```env
GAOKAO_AGENT_ADMIN_TOKEN=dev-admin-token
GAOKAO_AGENT_DATABASE_URL=sqlite:///./data/gaokao-agent.db
GAOKAO_AGENT_LLM_PROVIDER=openai_compatible
GAOKAO_AGENT_LLM_BASE_URL=https://your-openai-compatible-base-url/v1
GAOKAO_AGENT_LLM_API_KEY=replace-with-your-api-key
GAOKAO_AGENT_LLM_MODEL=replace-with-your-model
GAOKAO_AGENT_SMART_ANALYSIS_MODE=gated
GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=
```

智能分析模式：

- `off`：完全关闭模型增强分析，只返回规则兜底。
- `gated`：只允许拥有 `smart_analysis` 权益的用户调用模型。
- `on`：所有用户都可以调用模型增强分析。

### Web 配置

Web 环境变量示例文件：

- [apps/web/.env.example](apps/web/.env.example)

常用配置：

```env
GAOKAO_AGENT_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_GAOKAO_AGENT_API_URL=http://127.0.0.1:8000
GAOKAO_AGENT_ADMIN_TOKEN=dev-admin-token
```

注意：Web 的 `GAOKAO_AGENT_ADMIN_TOKEN` 必须和 API 的 `GAOKAO_AGENT_ADMIN_TOKEN` 保持一致，否则管理后台请求会被拒绝。

## 接入大模型

本项目的大模型调用通过 OpenAI 兼容接口完成。只要服务商支持 `/v1/chat/completions` 风格接口，就可以通过下面变量接入：

```env
GAOKAO_AGENT_LLM_PROVIDER=openai_compatible
GAOKAO_AGENT_LLM_BASE_URL=https://your-provider.example/v1
GAOKAO_AGENT_LLM_API_KEY=your-api-key
GAOKAO_AGENT_LLM_MODEL=your-model-name
GAOKAO_AGENT_SMART_ANALYSIS_MODE=gated
```

调用失败时系统会识别并记录常见原因：

- `provider_not_configured`
- `provider_request_failed`
- `provider_insufficient_balance`
- `provider_invalid_response`
- `smart_analysis_disabled_globally`
- `smart_analysis_entitlement_required`

## 张雪峰 Skill

如果需要本地技能文件，可以在仓库根目录执行：

```powershell
git clone https://github.com/alchaincyf/zhangxuefeng-skill.git vendor/zhangxuefeng-skill
```

当 `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH` 为空时，API 会自动尝试：

- `vendor/zhangxuefeng-skill/SKILL.md`
- `.tmp/zhangxuefeng-skill/SKILL.md`

## 微信公众号接入

后端提供公众号回调端点：

- `GET /api/chat/channels/wechat/official-account`
- `POST /api/chat/channels/wechat/official-account`

需要在 API `.env` 中配置：

```env
GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN=replace-with-your-wechat-token
GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID=wx-replace-with-your-app-id
GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY=replace-with-43-char-aes-key
```

本地公众号回调冒烟测试：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-wechat-official-account.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000 `
  -ApiEnvFilePath apps\api\.env
```

AES 调试辅助：

```powershell
python scripts/wechat_aes_helper.py decrypt `
  --value "<Encrypt payload>" `
  --app-id "<wechat app id>" `
  --encoding-aes-key "<43-char aes key>"
```

## 验证与测试

完整验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
```

单独运行 API 测试：

```powershell
cd apps/api
python -m pytest -q
```

单独运行 Web 测试和构建：

```powershell
cd apps/web
npm test --
npm run build
npm audit --audit-level=moderate
```

## 部署参考

- Windows 运行说明：[deploy/windows/README.md](deploy/windows/README.md)
- Linux 部署模板：[deploy/linux/README.md](deploy/linux/README.md)
- 本地交接手册：[docs/operations/local-handover-runbook.md](docs/operations/local-handover-runbook.md)

## 安全注意事项

- 不要提交 `.env`、`.env.local`、API Key、公众号 Token、AES Key 或数据库文件。
- `.gitignore` 已忽略 `.env`、`.env.local`、`.env.*.local`、`.tmp/`、`.venv/`、本地数据库和本地技能目录。
- 示例文件只放占位符，不应写入真实密钥。
- 生产环境请替换默认 `dev-admin-token`。

## 当前验证状态

最近一次本地验证结果：

- API 测试：`152 passed`
- Web 测试：`27 passed` test files，`124 passed` tests
- Web 构建：Next.js `15.5.19` production build 成功
- Web 安全审计：`npm audit --audit-level=moderate`，`0 vulnerabilities`

## 适合写入简历的项目摘要

高考填志愿.agent 是一个面向高考志愿咨询场景的全栈智能问答系统，基于 FastAPI、Next.js、SQLite 和 OpenAI 兼容大模型接口构建。项目实现了高考问答入口、张雪峰风格 Skill 路由、大模型结构化分析、规则兜底、智能分析权益控制、公众号回调、微信 AES 安全模式、媒体分析预留能力和运营管理后台。系统重点解决垂直咨询场景中模型调用不稳定、用户权益控制、公众号接入和本地可运行交付等问题，并配套自动化测试、生产构建、冒烟测试和部署模板，具备从本地 MVP 到后续线上部署的扩展基础。
