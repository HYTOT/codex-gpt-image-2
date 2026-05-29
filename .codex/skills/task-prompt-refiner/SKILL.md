---
name: task-prompt-refiner
description: Refine an existing structured `task_prompt.md` in this repository to improve image quality while preserving the task goal. Use when a task already runs but the prompt needs clearer decomposition, stronger priorities, or sharper constraints.
---

# Task Prompt Refiner

## Overview

Refine the task prompt, not the whole project.

Keep the existing task goal intact and improve clarity, separation of dimensions, and execution stability.

## Workflow

1. Read the current `task_prompt.md`.
2. Read related `raw_task.md` and, if relevant, output evidence such as `metadata.json`, `api/request.json`, `api/response.json`, and `logs/task.log`.
3. Identify where important requirements are compressed together or where priorities are ambiguous.
4. Rewrite the prompt in six sections with 3 to 5 bullets per section.
5. Split composition, subject identity, detail rules, usage, constraints, and priority into separate bullets.
6. Preserve the task's actual intent and language domain.

## Refinement Priorities

- Make each bullet carry one dominant dimension.
- Move high-impact must-have rules into `特别要求`.
- Move known failure modes into `约束`.
- For multi-reference tasks, explicitly assign reference responsibilities.
- Tighten text requirements when the task depends on visible Chinese words or symbols.

## Quality Checks

Confirm all of the following:

- still exactly six sections
- each section has 3 to 5 bullets
- no cross-task revision wording
- no semantic drift away from the original task goal
- priorities are explicit when multiple requirements may compete

## Not Responsible For

- Do not change `task.json` unless the request explicitly includes configuration changes.
- Do not diagnose API authentication or network failures here.
- Do not run image generation unless explicitly asked.
