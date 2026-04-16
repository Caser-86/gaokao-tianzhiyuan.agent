# WeChat Official Account Smoke Design

## Goal

Create a callback-only smoke script that operators can run against local,
staging, or production-style API endpoints without also probing unrelated web,
admin, or chat surfaces.

## Scope

- add a standalone PowerShell script for official-account callback verification
- support plaintext and AES probes independently
- allow the script to reuse `apps/api/.env` or explicit credentials
- keep the existing all-in-one local smoke script unchanged for now

## Decisions

- expose a focused `scripts/smoke-wechat-official-account.ps1` entry point
- keep argument resolution consistent with the existing local-stack scripts:
  explicit arg, env file, dev fallback
- default to a meaningful callback acceptance set: plaintext verify/text/event
  probes plus AES verify/text probes
- support `-SkipPlaintextProbes` and `-SkipAesProbes` so operators can match the
  mode they are actively wiring
