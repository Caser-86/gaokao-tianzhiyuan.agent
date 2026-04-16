# Local Stack Env File Design

## Goal

Make the local startup and smoke scripts work cleanly with operator-managed env
files so the MVP can be started and validated without editing script internals.

## Requirements

- `scripts/start-local-stack.ps1` should auto-load `apps/api/.env` and
  `apps/web/.env.local` when present.
- Both scripts should still allow explicit overrides through parameters.
- Startup output and persisted state must avoid exposing raw admin tokens or
  WeChat callback secrets.
- `scripts/smoke-local-stack.ps1` should validate the current built-in skill
  surface, not just the legacy ZhangXueFeng path.

## Decisions

- Use simple `KEY=value` env-file parsing directly inside the PowerShell scripts.
- Resolve settings with this priority: explicit argument, env file, dev fallback.
- Mask secrets in console output and omit them from the saved state file.
- Require `zhangxuefeng` and `catalog_lookup` in the skill-list smoke probe by
  default, while keeping an override parameter for future extensions.
