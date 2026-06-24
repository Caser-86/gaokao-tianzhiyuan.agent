# syntax=docker/dockerfile:1

# 1. 依赖安装层（全量依赖，含构建工具）
FROM node:20-alpine AS deps
WORKDIR /app/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
COPY apps/web/vendor ./vendor
RUN npm ci

# 2. 构建层
FROM node:20-alpine AS builder
WORKDIR /app/apps/web

COPY --from=deps /app/apps/web/node_modules ./node_modules
COPY apps/web/ . .

# 构建时环境变量（Next.js 内联到客户端）
ARG NEXT_PUBLIC_GAOKAO_AGENT_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_GAOKAO_AGENT_API_URL=$NEXT_PUBLIC_GAOKAO_AGENT_API_URL

RUN npm run build

# 3. 运行层（仅生产依赖，最小化镜像）
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# 非 root 用户运行
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# 运行时仅安装生产依赖
COPY apps/web/package.json apps/web/package-lock.json ./
COPY apps/web/vendor ./vendor
RUN npm ci --omit=dev

COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next ./.next
COPY --from=builder /app/apps/web/next.config.mjs ./next.config.mjs

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000/ >/dev/null 2>&1 || exit 1

CMD ["node", "./node_modules/next/dist/bin/next", "start", "-p", "3000"]
