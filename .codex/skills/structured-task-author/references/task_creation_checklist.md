# 结构化任务创建检查单

1. 任务目录是否放在 `tasks/<task-name>/`
2. 是否存在 `raw_task.md`
3. 是否存在 `task_prompt.md`
4. 是否存在 `task.json`
5. `task_prompt.md` 是否为固定 6 段
6. 每段是否为 3 到 5 条
7. 是否拆开了构图、主体、细节、用途、约束、优先级
8. 是否避免了跨任务修订语气
9. `task.json` 是否只使用当前支持的 5 个字段
10. `configs/task.json` 是否已经切到目标任务
