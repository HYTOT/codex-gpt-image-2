# 测试与 Smoke Check 清单

本文档只记录当前仓库真实在用的验证动作，以及它们分别证明什么、不证明什么。

## 最常用的 5 个检查

### 1. 运行结构化任务测试

```bash
python -m pytest tests/test_task_prompt_modes.py -q
```

证明什么：

- 结构化任务配置加载正常
- `raw_task.md` / `task_prompt.md` 的最小非空检查正常
- request / metadata 的关键字段写入正常
- `RUN_MODE=test -> quality=low` 行为正常

不证明什么：

- 不证明真实 API 可用
- 不证明当前任务提示词质量一定高

### 2. 运行认证诊断测试

```bash
python -m pytest tests/test_auth_check.py -q
```

证明什么：

- 独立认证检查入口可用
- 认证异常提示包装逻辑正常

不证明什么：

- 不证明你当前 `.env` 里的 key 一定有效

### 3. 运行全部当前测试

```bash
python -m pytest tests/test_task_prompt_modes.py tests/test_auth_check.py -q
```

证明什么：

- 当前最核心的结构化任务链路和认证诊断链路都没有明显回归

### 4. 语法编译检查

```bash
python -m compileall src tests main.py
```

证明什么：

- Python 语法和基本导入层面没有明显错误

不证明什么：

- 不证明运行时业务逻辑正确
- 不证明 API 调用一定成功

### 5. 独立认证检查

```bash
python -m src.api.auth_check
```

证明什么：

- 当前 `.env` 中的 `OPENAI_API_KEY` 是否被平台接受

不证明什么：

- 不证明某个具体任务提示词质量
- 不证明参考图和 mask 一定配置正确

## 任务提示词分段扫描

适用场景：

- 批量改写了 `tasks/*/task_prompt.md` 后
- 想确认所有任务都满足当前 6 段、每段 3 到 5 条的规范

建议检查内容：

- 每个任务是否有 6 个 `##`
- 每段 bullet 数是否都在 3 到 5 之间
- 是否存在空段、标题缺失或明显机械拆句

## 最小 smoke run

适用场景：

- 代码逻辑没改太多，但你想确认真实主流程还能跑

推荐做法：

1. 选一个参考图少、结构清楚的任务
2. 先跑 `python -m src.api.auth_check`
3. 再执行 `python main.py`
4. 检查最新输出目录里的 `metadata.json`、`request.json`、`response.json`

不建议：

- 在未确认 key 可用时，直接把主流程失败都归因给提示词或素材

## 建议的组合检查

### 改了 docs / task_prompt.md

至少跑：

- `python -m pytest tests/test_task_prompt_modes.py -q`
- 任务分段扫描

### 改了认证或 API 调用

至少跑：

- `python -m pytest tests/test_auth_check.py -q`
- `python -m src.api.auth_check`

### 改了主流程或输出链路

至少跑：

- `python -m pytest tests/test_task_prompt_modes.py tests/test_auth_check.py -q`
- `python -m compileall src tests main.py`
- 条件允许时补一轮真实 smoke run

## 验证结果怎么写进提交说明

建议最少写清：

- 跑了哪些命令
- 结果是通过、失败还是预期失败
- 如果是 `auth_check`，返回了哪个 `status`
- 如果没跑真实主流程，明确说明没有跑

## 相关文档

- [认证与接口排查手册](./auth_and_api_troubleshooting.md)
- [输出目录验收与复盘手册](./output_inspection_runbook.md)
