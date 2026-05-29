---
name: structured-task-author
description: Create or update a structured image generation task under this repository's `tasks/` directory. Use when Codex needs to turn a user's raw Chinese image request into `raw_task.md`, a six-section `task_prompt.md`, a minimal `task.json`, and an updated `configs/task.json` entry for this project.
---

# Structured Task Author

## Overview

Create repository-native image tasks for `codex-gpt-image-2`.

Always write outputs into `tasks/<task-name>/` and keep the task compatible with the current structured mode.

## Workflow

1. Read the user's raw request and determine task name, image ratio, whether reference images are required, and whether mask editing is needed.
2. Write `raw_task.md` as a concise archive of the original request intent. Do not send it to the model directly.
3. Write `task_prompt.md` in fixed six-section format:
   `场景 / 主体 / 关键细节 / 用途 / 约束 / 特别要求`
4. Ensure each section has 3 to 5 `-` items, each item is a complete Chinese instruction sentence, and different dimensions are split across different bullets.
5. Create the minimal `task.json` with only `reference_images`, `mask_image`, `image_size`, `image_format`, and `image_count`.
6. Update `configs/task.json` so `task_file` points to the new task.
7. Self-check structure, wording, and path validity before stopping.

## Required Output

Create or update exactly these files when building a new task:

- `tasks/<task-name>/raw_task.md`
- `tasks/<task-name>/task_prompt.md`
- `tasks/<task-name>/task.json`
- `configs/task.json`

## Prompt Rules

- Treat every task as an independent new task.
- Avoid `弃用`、`改用`、`不再`、`上一轮`、`上个任务`、`上一版`、`之前那版`.
- Keep each bullet focused on one major dimension such as composition, subject identity, text requirements, constraints, or priority.
- Prefer explicit priority in `特别要求` when multiple constraints may compete.
- For multi-reference tasks, explicitly state which reference image controls face, body, pose, template, local symbol, or negative example semantics.

## Minimal `task.json` Rules

- `reference_images` must be a list of paths relative to the task directory.
- `mask_image` must be an empty string when unused.
- Keep `image_format` aligned with current project defaults unless the user clearly needs another format.
- Do not reintroduce deprecated fields such as `prompt_name`, `prompt_version`, `variables_file`, or `prompt_source`.

## Self-Check

Before finishing, verify all of the following:

- The task has exactly six `##` sections.
- Each section has 3 to 5 bullets.
- Each bullet is a complete Chinese sentence with moderate length.
- `task.json` paths are relative to the task directory.
- `configs/task.json` points to the intended task.

## Not Responsible For

- Do not run image generation unless explicitly asked.
- Do not diagnose API failures here.
- Do not edit unrelated historical tasks unless the request is to refactor them too.
