# Local Stack Env File Implementation Plan

**Goal:** Finish the local operator loop so startup and smoke checks can reuse
real env files safely.

## Tasks

- Update `scripts/start-local-stack.ps1` to load default or explicit env files,
  resolve runtime settings from them, and keep startup diagnostics secret-safe.
- Update `scripts/smoke-local-stack.ps1` to reuse the API env file and verify
  both built-in chat skills.
- Refresh the Windows, Linux, and handover docs so operators know the new
  default behavior and override options.
- Run dry-run and project verification commands before closing the task.
