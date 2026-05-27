# AGENTS.md

## 项目定位

本项目是一个基于 Python 的 GPT Image 2 图片生成任务工程，当前阶段只实现脚本运行，不扩展服务端或前端界面。

项目核心目标：

1. 使用六段式结构化任务提示词管理图片生成任务。
2. 支持读取 `raw_task.md` 与 `task_prompt.md`。
3. 支持使用一个或多个本地参考图生成图片，并支持可选 mask 编辑。
4. 每次生成任务自动创建独立输出目录。
5. 自动保存图片、原始提示词、最终提示词、请求 JSON、响应 JSON、日志和 metadata。
6. 通过日志系统完整接管接口请求、响应、耗时与异常。
7. 保持项目结构清晰，方便后续扩展为 CLI、FastAPI 服务或 Web 管理后台。

---

## 最高原则

所有开发任务必须遵守以下优先级：

1. 安全与真实性优先。
2. 最小改动。
3. 先理解再修改。
4. 不乱动无关文件。
5. 优先保持现有风格。
6. 必须自检。
7. 禁止硬编码 API Key。
8. 禁止日志泄露密钥。
9. 禁止删除历史生成结果。
10. 禁止覆盖已有输出文件。
11. 禁止凭空假定 API 参数。
12. API 参数必须以当前项目依赖、OpenAI SDK、官方文档或已有实现为准。

---

## 技术栈

主要技术栈：

```text
Python
```

允许按需引入：

1. `openai`
2. `python-dotenv`
3. `pytest`
4. `pydantic`
5. `PyYAML`
6. `rich`

依赖原则：

1. 能用标准库解决的，不优先引入第三方库。
2. 引入新依赖前，先检查项目是否已有同类依赖。
3. 不为小功能引入过重依赖。
4. 新增依赖必须同步更新 `requirements.txt`。

---

## 目录规范

项目结构：

```text
codex-gpt-image-2/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── configs/
├── docs/
├── tasks/
├── src/
├── outputs/
├── logs/
└── tests/
```

目录职责：

1. `configs/`：运行入口配置与默认配置。
2. `docs/`：使用文档。
3. `tasks/`：结构化任务目录。
4. `src/api/`：API 调用封装。
5. `src/config/`：配置读取。
6. `src/core/`：核心业务流程。
7. `src/logger/`：日志系统封装。
8. `src/utils/`：通用工具函数。
9. `outputs/`：每次图片生成任务的输出目录。
10. `logs/`：全局日志。
11. `tests/`：测试目录。

---

## 结构化任务模式

运行时只支持结构化任务目录：

```text
tasks/<任务名>/
├── task.json
├── raw_task.md
├── task_prompt.md
├── reference_images/
└── mask/
```

说明：

1. `raw_task.md`：原始需求归档，不直接发给模型。
2. `task_prompt.md`：最终执行提示词。
3. `reference_images/` 与 `mask/`：可选输入素材目录。

`task.json` 当前仅允许以下字段：

```json
{
  "reference_images": [],
  "mask_image": "",
  "image_size": "3840x2160",
  "image_format": "png",
  "image_count": 1
}
```

要求：

1. 禁止继续使用 `prompt_name`、`prompt_version`、`variables_file`、`prompt_source`。
2. `configs/task.json` 只允许保留 `task_file` 指针。
3. 旧模板模式已经弃用，禁止再新增任何兼容入口。

---

## 六段式提示词规范

`task_prompt.md` 必须固定包含以下标题，顺序不能变：

```md
## 场景
## 主体
## 关键细节
## 用途
## 约束
## 特别要求
```

规则：

1. 每个 `##` 下必须有 3 到 5 个 `-` 条目。
2. 单条 `-` 必须是完整中文提示句，长度适中、信息密度高，不要把多个维度硬塞进一条过长散文句。
3. 每个任务默认视为独立新任务。
4. 不允许出现 `弃用`、`改用`、`不再`、`上一轮`、`上个任务`、`上一版`、`之前那版`。
5. 以上结构要求属于 Codex 新建任务时必须直接写对的内容，不得依赖运行时代码兜底纠正。

---

## 新增生图任务 Checklist

Codex 新增任务时，必须按以下顺序执行：

1. 先理解需求，再新建 `tasks/<任务名>/raw_task.md`，只做原始需求归档，不直接发给模型。
2. 再写 `tasks/<任务名>/task_prompt.md`，直接产出合规六段式最终提示词，确保每节 3 到 5 条、长度适中、信息维度分开表达、默认独立新任务、避免跨任务修订语气。
3. 自查 `task_prompt.md` 结构和语气无误后，再更新 `tasks/<任务名>/task.json` 与 `configs/task.json` 的 `task_file` 指针。

---

## 输出目录规范

每次生成任务必须创建独立目录：

```text
outputs/YYYY-MM-DD/YYYYMMDD_HHMMSS_task_xxxxx/
```

任务目录内必须包含：

```text
images/
prompt/
api/
logs/
inputs/
metadata.json
```

其中固定文件：

```text
prompt/raw_prompt.md
prompt/final_prompt.md
api/request.json
api/response.json
logs/task.log
metadata.json
```

要求：

1. 不得覆盖历史任务目录。
2. 不得删除历史生成结果。
3. 每次任务必须有唯一 `task_id`。
4. 任务失败时也必须保留已生成的中间文件。

---

## metadata.json 规范

每次任务必须生成 `metadata.json`。

推荐字段：

```json
{
  "task_id": "20260512_213045_task_xxxxx",
  "created_at": "2026-05-12 21:30:45",
  "updated_at": "2026-05-12 21:30:45",
  "model": "gpt-image-2",
  "prompt_source_mode": "structured_markdown",
  "source_task_prompt": "tasks/example/task_prompt.md",
  "source_raw_task": "tasks/example/raw_task.md",
  "output_dir": "outputs/2026-05-12/20260512_213045_task_xxxxx",
  "image_paths": [],
  "request_path": "api/request.json",
  "response_path": "api/response.json",
  "task_log_path": "logs/task.log",
  "status": "pending",
  "duration_ms": 0,
  "error": null
}
```

---

## API 调用规范

1. API Key 必须从环境变量或安全配置中读取。
2. 禁止硬编码 API Key。
3. 禁止在日志中输出完整 API Key。
4. 禁止在请求 JSON 中保存 API Key。
5. 禁止在响应 JSON 中写入敏感 Header。
6. 请求参数必须保存到 `api/request.json`。
7. 响应结果必须保存到 `api/response.json`。
8. 图片必须保存到 `images/`。
9. 如使用参考图，必须保存 `inputs/reference/` 与 `inputs/mask/` 快照。
10. 请求失败时必须记录错误与异常堆栈。
11. `RUN_MODE=test` 下图片质量必须强制使用 `low`。
12. 请求 JSON 必须记录 `prompt_source_mode`、`source_task_prompt`、`source_raw_task`。

---

## 日志规范

全局日志：

```text
logs/app.log
```

任务日志：

```text
outputs/YYYY-MM-DD/task_id/logs/task.log
```

日志必须记录：

1. 任务开始时间。
2. 任务 ID。
3. 使用模型。
4. 输出目录。
5. 请求参数摘要。
6. 响应摘要。
7. 图片保存路径。
8. 请求耗时。
9. 总耗时。
10. 错误信息。
11. 异常堆栈。

日志中禁止出现：

1. API Key。
2. Token。
3. Secret。
4. Authorization Header。
5. 未脱敏环境变量。
6. 用户本地敏感绝对路径。

---

## Python 文件规范

所有 Python 文件必须使用 UTF-8 编码。

新建或真实修改 Python 文件时，必须添加或更新头注释：

```python
# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: YYYY-MM-DD HH:mm:ss
@LastEditor: Ajax
@LastEditTime: YYYY-MM-DD HH:mm:ss
@Description: 文件职责描述
"""
```

要求：

1. `@Author` 固定为 `Ajax`。
2. `@LastEditor` 固定为 `Ajax`。
3. 时间使用北京时间。
4. `@Description` 必须准确描述文件职责。
5. 修改已有文件时，更新 `@LastEditTime`。

---

## 核心模块职责

### settings.py

1. 读取环境变量。
2. 读取默认配置。
3. 提供模型名、图片尺寸、输出目录等配置。
4. 检查 `OPENAI_API_KEY` 是否存在。
5. 不直接执行 API 请求。

### task_config.py

1. 读取 `configs/task.json` 或 `configs/task.example.json`。
2. 解析 `task_file` 指针。
3. 校验结构化任务 schema。
4. 解析 `raw_task.md`、`task_prompt.md`、参考图和可选 mask。

### prompt_engine.py

1. 读取 Markdown 提示词。
2. 对 `raw_task.md` 与 `task_prompt.md` 做最小存在性与非空检查，并统一换行。
3. 不做模板渲染。
4. 不做变量替换。

### generator.py

1. 读取结构化任务。
2. 落盘 `raw_prompt.md` 与 `final_prompt.md`。
3. 调用图片 API。
4. 保存请求、响应、图片、日志和 metadata。
5. 捕获异常并保留中间文件。

### task_manager.py

1. 创建任务 ID。
2. 创建任务目录和固定子目录。
3. 初始化与更新结构化任务 metadata。
4. 避免覆盖历史任务目录。

---

## 错误处理规范

以下情况必须处理并记录日志：

1. 配置缺失。
2. API Key 缺失。
3. `raw_task.md` 不存在。
4. `task_prompt.md` 不存在。
5. JSON 解析失败。
6. `raw_task.md` 或 `task_prompt.md` 为空。
7. API 请求失败。
8. API 响应异常。
9. 图片保存失败。
10. 目录创建失败。
11. 日志写入失败。
12. metadata 更新失败。

错误发生时必须：

1. 写入任务日志。
2. 写入全局日志。
3. 更新 `metadata.json`。
4. 保留已生成中间文件。
5. 不删除历史输出。
6. 不覆盖已有文件。

---

## 禁止事项

严禁：

1. 硬编码 API Key。
2. 日志泄露密钥。
3. 删除历史生成结果。
4. 覆盖已有输出文件。
5. 恢复旧模板模式兼容。
6. 修改无关文件。
7. 大范围格式化项目。
8. 引入无必要的新框架。
9. 吞掉异常不记录。
10. 把所有逻辑堆在一个文件。
11. 破坏六段式任务规范。

---

## 开发流程

1. 阅读相关文件。
2. 判断影响范围。
3. 制定最小改动方案。
4. 修改必要文件。
5. 如涉及新任务，先写 `raw_task.md`，再直接写对六段式 `task_prompt.md`，最后再更新 `task.json` 与 `configs/task.json`。
6. 补充必要注释。
7. 检查语法。
8. 检查日志。
9. 检查输出目录。
10. 检查敏感信息是否脱敏。
11. 汇总修改结果。

---

## 自检要求

完成开发后，至少检查：

1. Python 语法是否正确。
2. import 是否正确。
3. 路径是否跨平台。
4. 配置缺失时是否有明确错误。
5. API Key 是否不会进入日志。
6. 请求 JSON 是否保存。
7. 响应 JSON 是否保存。
8. `prompt_source_mode` 与提示词来源路径是否写入请求快照和 `metadata.json`。
9. 如本次新增或修改任务，`task_prompt.md` 是否在创建阶段已满足六段式标题、每节 3 到 5 条、长度适中且信息维度分开的要求，并避开禁用话术。
10. `RUN_MODE=test` 时图片质量是否强制为 `low`。
11. 图片是否保存到独立任务目录。
12. 当前任务日志是否保存。
13. 异常堆栈是否保存。
14. `metadata.json` 是否更新。
15. 历史输出是否不会被覆盖。
16. 是否没有改动无关文件。
17. 是否没有重新引入旧模板兼容。

---

## 交付格式

每次完成任务后，按以下格式回复：

```md
## 修改摘要

- ...

## 修改文件

- ...

## 核心实现

- ...

## 自检结果

- ...

## 风险或未完成

- ...
```

如果没有风险，写：

```md
## 风险或未完成

- 暂无
```
