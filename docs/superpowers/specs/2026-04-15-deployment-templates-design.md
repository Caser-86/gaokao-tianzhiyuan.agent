# Deployment Templates Design

## Goal

Add deployment-oriented templates and operator documentation that make the current
Gaokao Agent MVP easier to run in two environments:

- Windows 11 for local long-running usage
- Linux servers for production-style deployment

The goal is not to deploy directly onto a real machine in this task. The goal is
to produce reusable scripts, templates, and runbooks that reduce setup work and
make handoff safer.

## Scope

This design covers two deployment tracks that share the same application layout:

- `apps/api` as the FastAPI backend
- `apps/web` as the Next.js frontend

### In scope

- Windows 11 startup, stop, and logging templates
- Windows 11 operator documentation
- Linux deployment templates based on `systemd` and `nginx`
- Linux environment file examples and deployment runbook
- Clear separation between local development scripts and deployment-oriented
  operator assets

### Out of scope

- Direct modification of real machine services
- HTTPS certificate provisioning
- Docker or Docker Compose
- WeChat production callback wiring
- Cloud-specific infrastructure automation

## Constraints

- Keep the current local workflow working:
  - `scripts/start-local-stack.ps1`
  - `scripts/smoke-local-stack.ps1`
  - `scripts/verify-project.ps1`
- Do not require Docker
- Keep secrets out of git-tracked files
- Prefer operator-friendly templates over heavily abstracted automation

## Users

There are two main operators:

1. The current Windows user who wants the project to keep running reliably on a
   local Windows 11 machine.
2. A future Linux operator who wants a standard server-style deployment layout
   with service management, reverse proxying, and predictable logs.

## Approach Options

### Option 1: Windows only first, Linux later

This would optimize for speed right now, but it leaves the production path only
half documented.

### Option 2: Linux only first, Windows later

This would optimize for formal deployment, but it would not match the user's
current environment and would delay the most immediately useful delivery.

### Option 3: Two-track templates in one pass

This creates a Windows operating path and a Linux operating path in parallel,
while keeping them clearly separated in docs and file layout.

### Recommendation

Use option 3.

Reasoning:

- It matches the user's current Windows needs
- It keeps a production-style Linux path ready for later
- It avoids forcing one environment to mimic the other
- It delivers reusable operator artifacts without increasing runtime complexity

## Design

### Windows 11 track

The Windows deployment track should build on the existing PowerShell-based
tooling and add "operator mode" scripts rather than replacing development
scripts.

Planned artifacts:

- a production-like Windows env template for API
- a production-like Windows env template for Web
- a stop script that can cleanly stop the locally launched stack by pid or
  stored state
- a Windows deployment runbook that explains:
  - preparing env files
  - starting the stack
  - stopping the stack
  - log file locations
  - optional Task Scheduler guidance for auto-start

The Windows track should remain script-first and avoid Windows service
registration in this phase. That keeps it portable and low-risk while still
being useful for long-running local usage.

### Linux track

The Linux deployment track should provide standard text templates instead of
machine-specific installers.

Planned artifacts:

- `systemd` service unit template for the API
- `systemd` service unit template for the Web app
- `nginx` site config template that routes:
  - `/` to the Web app
  - API requests to the backend
- Linux production env examples for API and Web
- a Linux deployment runbook that explains:
  - directory layout assumptions
  - env file placement
  - service enable/start/restart flow
  - nginx enable/reload flow
  - basic smoke checks and rollback checks

This track should assume a generic Linux VM and not depend on any one cloud.

## File Layout

Recommended new structure:

- `deploy/windows/`
  - Windows-oriented env examples or notes
  - Windows runbook
- `deploy/linux/`
  - `systemd` unit templates
  - `nginx` config template
  - Linux env examples or notes
  - Linux runbook
- `scripts/`
  - runtime helper scripts only

This keeps deployment material separate from development scripts and makes later
handoff easier.

## Operational Flow

### Windows flow

1. Copy env example files
2. Fill secrets locally
3. Run local startup script
4. Optionally run smoke checks
5. Keep logs in `.tmp/`
6. Stop the stack through the provided stop path

### Linux flow

1. Prepare app directory and env files
2. Build the Web app
3. Configure `systemd` units
4. Configure `nginx`
5. Start and enable services
6. Run health checks and smoke checks

## Error Handling

The templates and docs should explicitly cover:

- API env mismatch
- admin token mismatch between API and Web
- relay not configured
- relay insufficient balance
- Web build warning caused by blocked native SWC on Windows
- logs to inspect first when startup fails

## Testing Strategy

This work is mainly scripts and docs, so verification should be operator-focused.

Required verification:

- syntax check new PowerShell scripts
- use real execution for any new Windows startup or stop flow
- use existing `scripts/verify-project.ps1`
- ensure deployment templates remain text-only and do not break the app

## Success Criteria

This design is successful when:

- a Windows operator can start, stop, and inspect the stack using repo assets
- a future Linux operator has clear `systemd` and `nginx` templates to adapt
- the repo contains environment examples for both operating contexts
- deployment guidance is separated from local dev guidance but linked from the
  main docs
