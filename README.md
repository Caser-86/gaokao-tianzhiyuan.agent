# Gaokao Agent

高考志愿项目当前包含两部分：

- `apps/api`
  FastAPI 后端，提供公开内容、管理后台、平台权益、聊天技能网关。
- `apps/web`
  Next.js 前端，提供首页、学校/专业详情、轻量聊天页和管理后台。

## 项目现状

当前代码库已经具备：

- 公开内容浏览
- 管理后台内容运营能力
- 智能分析全局开关与按用户权益控制
- `zhangxuefeng` 技能接入 OpenAI 兼容接口
- Web `/chat` 入口与 API 聊天网关联动

## 目录

```text
apps/
  api/   FastAPI backend
  web/   Next.js frontend
data/    本地数据与 SQLite 文件
docs/    设计与实施文档
vendor/  本地下载的外部技能或依赖资产
```

## 快速启动

### 1. 启动 API

```powershell
cd apps/api
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

API 健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/chat/health
```

### 2. 启动 Web

```powershell
cd apps/web
Copy-Item .env.example .env.local
npm install
npm run dev
```

默认地址：

- Web: `http://127.0.0.1:3000`
- Admin: `http://127.0.0.1:3000/admin`
- Chat: `http://127.0.0.1:3000/chat`

Detailed operator checklist:

- `docs/operations/local-handover-runbook.md`

## 环境变量

### API

API 环境变量参考：

- [apps/api/.env.example](/D:/Program Files/gaokao-agent/.worktrees/codex-gaokao-mvp/apps/api/.env.example)

关键变量：

- `GAOKAO_AGENT_ADMIN_TOKEN`
- `GAOKAO_AGENT_DATABASE_URL`
- `GAOKAO_AGENT_LLM_PROVIDER`
- `GAOKAO_AGENT_LLM_BASE_URL`
- `GAOKAO_AGENT_LLM_API_KEY`
- `GAOKAO_AGENT_LLM_MODEL`
- `GAOKAO_AGENT_SMART_ANALYSIS_MODE`
- `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH`

### Web

Web 环境变量参考：

- [apps/web/.env.example](/D:/Program Files/gaokao-agent/.worktrees/codex-gaokao-mvp/apps/web/.env.example)

关键变量：

- `GAOKAO_AGENT_API_URL`
- `NEXT_PUBLIC_GAOKAO_AGENT_API_URL`
- `GAOKAO_AGENT_ADMIN_TOKEN`

说明：

- 服务端请求默认读取 `GAOKAO_AGENT_API_URL`
- 浏览器侧交互默认优先读取 `NEXT_PUBLIC_GAOKAO_AGENT_API_URL`
- 管理后台调用 API 时，Web 端的 `GAOKAO_AGENT_ADMIN_TOKEN` 要与 API 端保持一致

## 张雪峰技能

如果需要本地技能文件，可在仓库根目录执行：

```powershell
git clone https://github.com/alchaincyf/zhangxuefeng-skill.git vendor/zhangxuefeng-skill
```

当 `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH` 为空时，API 会自动尝试：

- `vendor/zhangxuefeng-skill/SKILL.md`
- `.tmp/zhangxuefeng-skill/SKILL.md`

## 验证命令

### API

```powershell
cd apps/api
python -m pytest -q
```

### Web

```powershell
cd apps/web
npm test --
npm run build
```

## 已知说明

- 在当前 Windows 环境下，Next 原生 SWC 二进制可能被系统策略拦截；项目已经启用 `useWasmBinary`，所以构建仍可成功。
- `.tmp/` 和 `vendor/zhangxuefeng-skill/` 是本地资产目录，已加入忽略规则，不会进入仓库提交。
