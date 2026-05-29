---
name: image-task-diagnoser
description: Diagnose a failed or suspicious image generation run in this repository. Use when Codex needs to inspect `metadata.json`, `api/request.json`, `api/response.json`, `logs/task.log`, and optional `python -m src.api.auth_check` output to classify the root cause and recommend the next step.
---

# Image Task Diagnoser

## Overview

Diagnose one output directory at a time.

Prefer the latest output directory only when the user does not specify a target path.

## Workflow

1. Start from `metadata.json` to determine task status, source task files, and top-level error summary.
2. Read `api/response.json` to see whether the platform returned image data or an error payload.
3. Read `logs/task.log` to recover timing, request summary, and stack trace.
4. Read `api/request.json` only after you know what failed, so you can confirm whether the request itself was wrong.
5. If the error looks authentication-related, run `python -m src.api.auth_check`.
6. End with a structured diagnosis: root cause class, supporting evidence, and next step.

## Root Cause Classes

Classify the run into one of these buckets when possible:

- authentication problem
- network/connectivity problem
- SDK compatibility problem
- task configuration problem
- prompt quality or prompt structure problem
- reference image or mask input problem
- response shape or image saving problem

## Evidence Order

Use this fixed evidence order:

1. `metadata.json`
2. `api/response.json`
3. `logs/task.log`
4. `api/request.json`
5. `prompt/` and `inputs/` when needed

## What To Report

Always report:

- final task status
- most likely root cause
- exact file path(s) used as evidence
- whether the issue is before request, during request, or after response
- one concrete next action

## Special Rule For 401

If you see `401 invalid_api_key` or equivalent authentication errors:

- treat it as authentication-first, not prompt-first
- run `python -m src.api.auth_check` unless the user forbids commands
- state whether the independent auth check confirms the same failure

## Not Responsible For

- Do not automatically rewrite `task_prompt.md`
- Do not automatically change code
- Do not rerun the image task unless explicitly asked
