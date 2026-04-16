# WeChat Official Account Smoke Implementation Plan

**Goal:** Add a focused acceptance script for official-account callbacks.

## Tasks

- create `scripts/smoke-wechat-official-account.ps1` with env-file support,
  plaintext probes, and AES probes
- document local and remote usage in the API README, Windows notes, and
  handover runbook
- run dry-run plus a real local acceptance pass against the started stack
