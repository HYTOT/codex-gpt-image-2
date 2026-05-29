---
name: output-reviewer
description: Review a completed or failed output directory in this repository and produce a concise acceptance plus retrospective summary. Use when Codex needs to judge whether the result is usable and what should be improved next.
---

# Output Reviewer

## Overview

Review one output directory and summarize what happened, whether it is acceptable, and what should change next.

## Workflow

1. Read `metadata.json` for task status and source task files.
2. Read `prompt/raw_prompt.md` and `prompt/final_prompt.md` to compare original intent with executed prompt.
3. Read `api/request.json` and `api/response.json` to understand actual request and platform result.
4. Read `logs/task.log` for timing and failure context when needed.
5. If image files exist, evaluate whether the likely result meets the task's intended usage.
6. End with acceptance verdict, key strengths, key risks, and next-step recommendation.

## Output Format

Report at least:

- acceptance verdict: pass / conditional / fail
- whether the prompt is clear
- whether reference strategy seems well assigned
- whether request parameters match the task goal
- whether the next iteration should focus on prompt, assets, parameters, or auth/network

## Review Principles

- Prefer evidence from the output directory over assumptions from current working files.
- Separate execution failure from prompt-quality weakness.
- If the task failed before image generation, say that visual quality cannot yet be judged.

## Not Responsible For

- Do not silently change prompt files or code.
- Do not rerun the task unless explicitly asked.
