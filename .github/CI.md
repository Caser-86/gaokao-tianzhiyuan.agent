# CI/CD 配置

本项目使用 GitHub Actions 实现持续集成与持续交付。

## 工作流概览

### CI（[ci.yml](workflows/ci.yml)）

触发时机：`push` 到 `main`/`master` 分支，或针对这两个分支的 `pull_request`。

| Job | 说明 | 依赖 |
|-----|------|------|
| `api-lint` | ruff check + ruff format check + black check | - |
| `api-test` | alembic 迁移冒烟测试 + pytest | - |
| `web-lint` | ESLint 检查 | - |
| `web-test` | vitest 单元测试 | - |
| `web-build` | Next.js 生产构建 | `web-lint`, `web-test` |
| `docker-build` | 构建前后端 Docker 镜像（不推送） | `api-test`, `web-build` |

特性：
- 同分支并发任务自动取消旧运行（`concurrency`）
- pip / npm 依赖缓存
- Docker 构建使用 GitHub Actions 缓存（`cache-from: type=gha`）

### Release（[release.yml](workflows/release.yml)）

触发时机：推送 `v*.*.*` 格式的 tag（如 `v1.0.0`、`v1.0.0-rc.1`）。

| Job | 说明 |
|-----|------|
| `publish-images` | 构建 API/Web 镜像并推送到 GitHub Container Registry（ghcr.io） |
| `github-release` | 自动创建 GitHub Release，含自动生成的 changelog |

镜像 tag 策略：
- `latest`：最新版本
- `{version}`：如 `1.0.0`
- `{short_sha}`：commit 短哈希

## 使用方式

### 日常开发
```bash
git push origin feature-branch
# 自动触发 CI，在 PR 中查看检查状态
```

### 发布新版本
```bash
git tag v1.0.0
git push origin v1.0.0
# 自动触发 Release 工作流
```

### 拉取发布的镜像
```bash
docker pull ghcr.io/<owner>/gaokao-tianzhiyuan.agent/api:latest
docker pull ghcr.io/<owner>/gaokao-tianzhiyuan.agent/web:latest
```

## 本地复现 CI 检查

### API
```bash
cd apps/api
pip install -e ".[dev]"
ruff check .
ruff format --check .
black --check .
pytest tests/
```

### Web
```bash
cd apps/web
npm ci
npm run lint
npm test
npm run build
```
