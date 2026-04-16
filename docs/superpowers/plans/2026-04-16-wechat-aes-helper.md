# WeChat AES Helper Implementation Plan

**Goal:** Make the local AES helper easier to use and verify for official-account
callback debugging.

## Tasks

- update `scripts/wechat_aes_helper.py` so each subcommand validates only the
  arguments it actually needs
- simplify `scripts/smoke-local-stack.ps1` to call the helper with the reduced
  `sign` contract
- add direct API-side tests for the crypto module and helper CLI
- document manual sign, decrypt, and encrypt examples for operators
