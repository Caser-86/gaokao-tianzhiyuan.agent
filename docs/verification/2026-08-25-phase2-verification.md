# Phase 2 验证记录

## 范围与基线

- 日期：2026-08-25
- 基线 HEAD：`772948a6f6fe28b353007b009658e277f07475ed`
- 分支：`main`
- 状态：工作区包含用户原有未提交改动，以及本轮 Phase 2.2—2.8 的工作树改动；本记录不表示已经提交或发布。
- 环境：Windows PowerShell；Python 3.14.6 / pytest 9.1.1；Node.js v24.18.0 / npm 11.16.0。

没有读取或输出任何真实 `.env` 值、API Key、管理员 token 或微信公众号密钥。验证使用现有本地依赖、示例配置和 `https://api.example.com` 这一非真实域名构建参数。

## 已执行命令

| 命令 | 结果 |
|---|---|
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\smoke-local-stack.ps1 -DryRun -SkipAdminCheck -SkipChatProbe -SkipWechatProbe -SkipWechatOfficialAccountProbe` | Phase 2.1 修复后退出码 `0` |
| 使用示例配置运行 `scripts/start-local-stack.ps1 -RunSmoke`，再运行 `scripts/stop-local-stack.ps1 -StateFilePath .\\.tmp\\phase2-smoke.state.json` | API/Web/Chat/Admin/微信适配器/公众号明文与 AES smoke 退出码 `0`；停止命令退出码 `0` |
| `$env:Path = (Join-Path (Resolve-Path 'apps/api/.venv/Scripts') '') + ';' + $env:Path; powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify-project.ps1` | 退出码 `0`；基础校验、API/Web 测试、typecheck、覆盖率报告和生产构建全部完成 |
| `apps/api/.venv\\Scripts\\python.exe -m pytest -q`（在 `apps/api`） | `152 passed, 8 warnings`，退出码 `0`，6.78s |
| `npm run typecheck`（在 `apps/web`） | 独立源代码 TypeScript 检查退出码 `0`；测试目录不纳入该检查 |
| `npm run test:coverage`（在 `apps/web`） | `27` 个测试文件、`124` 个用例通过；V8 覆盖率：86.81% statements、84.34% branches、71.27% functions |
| `npm run lint`（在 `apps/web`） | 退出码 `0`；3 个既有 `<img>` 规则警告，无 lint error |
| `npm run build`（在 `apps/web`） | Next.js `15.5.19` 生产构建退出码 `0`；类型检查和静态页面生成通过 |
| `docker compose --env-file .env.docker.example config --quiet` | 退出码 `0` |
| `git diff --check` | 退出码 `0` |
| `apps/api/.venv\\Scripts\\python.exe scripts/verify-data-assets.py` | 根目录 `data/` 校验通过：2 所学校、4 个专业；提示 `apps/data` 为未验证重复目录 |
| `apps/api/.venv\\Scripts\\python.exe scripts/verify-data-assets.py --fail-on-legacy-duplicate` | 在当前工作区按预期因未跟踪 `apps/data/` 返回退出码 `1`；CI 干净 checkout 使用该严格模式，防止重复目录进入仓库 |
| `apps/api/.venv\\Scripts\\python.exe scripts/tests/test_verify_data_assets.py` | 1 个契约测试通过 |
| `apps/api/.venv\\Scripts\\python.exe -m pytest --cov=app --cov-report=term-missing -q` | `152 passed`；后端覆盖率 81% statements；覆盖率运行产生 15 个 warning |
| Phase 2.8 live smoke | 已验证公开首页、聊天页、后台页；Web chat POST 返回 `structured_json` 与 `chat_*` request id；后台智能分析设置返回合法模式 |

## 未完成或未能执行的验证

- `docker build --build-arg NEXT_PUBLIC_GAOKAO_AGENT_API_URL=https://api.example.com -f apps/web/Dockerfile ...` 未能开始构建：本机 Docker CLI 可用，但 Docker Desktop Linux daemon 不在运行，错误为 `failed to connect to the docker API ... dockerDesktopLinuxEngine`。
- GitHub Actions 的实际 tag Release 没有触发；本轮只静态验证了 `ci.yml` 暴露 `workflow_call`、`release.yml` 复用同一 workflow，并要求 production Environment 提供公开 API 地址。
- 覆盖率本轮只作为观察基线，尚未设置通过门槛；npm audit 仍报告 8 个漏洞，本轮没有自动执行 `npm audit fix`。
- 没有执行真实部署、HTTPS、迁移、发布后 smoke、监控告警或回滚演练。

## 异常执行记录

第一次与前端命令并行启动 API 全量测试时曾报告 `14 failed, 138 passed, 8 warnings`，失败集中为 `sqlite3.OperationalError: no such table: runtimesetting`。随后独立执行单测、全量 `pytest -x -vv` 和 `verify-project.ps1` 均通过，当前无法在独立重跑中复现；因此没有针对未复现症状修改业务代码，后续 CI 应继续观察是否出现同类环境耦合。

## 本轮配置收口

- `.github/workflows/ci.yml` 增加 `workflow_call`；Release 的 `ci-pass` 改为复用同一 commit 的 CI workflow，不再使用提示性 `echo`。
- `.github/workflows/release.yml` 为生产 Web 镜像增加公开 API URL 非空和协议校验，并从 `production` Environment 的 `NEXT_PUBLIC_GAOKAO_AGENT_API_URL` 读取构建参数。
- `apps/web/Dockerfile` 要求构建时显式传入公开 API 根地址；`docker-compose.yml` 对该变量改为必填。
- Linux 生产环境示例改为 API 根地址，代码会自动追加 `/api/...` 路径。
- `scripts/verify-data-assets.py` 以根目录 `data/` 为权威源，校验 JSON 结构、slug 唯一性、学校/专业关联、榜单字段和精选轮换引用；已接入 `verify-project.ps1` 与 CI。
- 本地未跟踪的 `apps/data/` 未删除；它不作为数据源，也不会进入干净 checkout。CI 通过 `--fail-on-legacy-duplicate` 拒绝将其提交进仓库。
