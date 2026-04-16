# WeChat AES Helper Design

## Goal

Tighten the local WeChat official-account AES debugging path so operators can
generate signatures and inspect encrypted payloads without memorizing extra
arguments.

## Scope

- make `scripts/wechat_aes_helper.py sign` require only the signature inputs
- keep `encrypt` and `decrypt` strict about `app_id` and `encoding_aes_key`
- add direct automated coverage for the crypto helpers and CLI contract
- document manual helper usage in operator-facing docs

## Decisions

- validate arguments per operation instead of marking every CLI flag globally
  required
- preserve the existing `encrypt / decrypt / sign` command surface
- test the CLI through real subprocess calls so the docs and operator workflow
  stay aligned with actual execution
