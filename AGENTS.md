# AGENTS.md

## 项目定位

本项目是一个基于 Python 的 GPT Image 2 图片生成提示词工程。

项目核心目标：

1. 管理提示词模板。
2. 管理提示词版本。
3. 支持模板变量替换。
4. 支持读取 Markdown 提示词文件。
5. 调用 GPT Image 2 API 生成图片。
6. 支持使用一个或多个本地参考图生成图片，并支持可选 mask 编辑。
7. 每次生成任务自动创建独立输出目录。
8. 自动保存图片、原始提示词、最终提示词、变量快照、请求 JSON、响应 JSON、日志和 metadata 元信息。
9. 通过日志系统完整接管接口请求、响应、耗时与异常。
10. 保持项目结构清晰，方便后续扩展为 CLI、FastAPI 服务或 Web 管理后台。
11. 当前阶段只实现 Python 脚本运行，不扩展服务端或前端界面。

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

非必要不增加其他技术栈。

允许按需引入：

1. `openai`：OpenAI 官方 SDK。
2. `python-dotenv`：本地开发环境变量读取。
3. `pytest`：基础测试。
4. `pydantic`：配置校验，只有确实需要时才引入。
5. `PyYAML`：YAML 配置支持，只有确实需要时才引入。
6. `rich`：命令行输出优化，只有确实需要时才引入。

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
├── prompts/
├── src/
├── outputs/
├── logs/
└── tests/
```

目录职责：

1. `configs/`：配置文件与提示词版本索引。
2. `prompts/templates/`：提示词模板。
3. `prompts/versions/`：提示词版本文件。
4. `prompts/variables/`：提示词变量文件。
5. `src/api/`：API 调用封装。
6. `src/config/`：配置读取。
7. `src/core/`：核心业务流程。
8. `src/logger/`：日志系统封装。
9. `src/utils/`：通用工具函数。
10. `outputs/`：每次图片生成任务的输出目录。
11. `logs/`：全局日志。
12. `tests/`：测试目录。

---

## 输出目录规范

每次生成任务必须创建独立目录。

目录格式：

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

具体文件：

```text
images/image_001.png
prompt/raw_prompt.md
prompt/final_prompt.md
prompt/variables.json
api/request.json
api/response.json
logs/task.log
inputs/reference/reference_001.png
inputs/mask/mask.png
metadata.json
```

要求：

1. 不得覆盖历史任务目录。
2. 不得删除历史生成结果。
3. 每次任务必须有唯一 `task_id`。
4. 任务失败时也必须保留已生成的中间文件。
5. 任务失败时必须写入 `metadata.json`，并将 `status` 标记为 `failed`。
6. 所有输出路径优先使用项目内相对路径记录。
7. 如果任务使用参考图，必须保存输入快照。

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
  "prompt_template": "default.md",
  "prompt_version": "default_v1.md",
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

## 提示词工程规范

项目需要支持：

1. 单个提示词直接生成图片。
2. 多套提示词模板管理。
3. 模板变量替换。
4. Markdown 提示词文件读取。
5. 提示词版本管理。

提示词模板目录：

```text
prompts/templates/
```

提示词版本目录：

```text
prompts/versions/
```

提示词变量目录：

```text
prompts/variables/
```

提示词版本索引：

```text
configs/prompt_versions.json
```

每次任务必须保存：

```text
prompt/raw_prompt.md
prompt/final_prompt.md
prompt/variables.json
```

说明：

1. `raw_prompt.md`：用户原始输入或原始模板内容。
2. `final_prompt.md`：变量替换完成后，最终提交给 API 的完整提示词。
3. `variables.json`：本次任务使用的变量快照。

---

## 模板变量规范

模板变量采用双花括号格式：

```text
{{variable_name}}
```

示例：

```md
# 图片生成任务

主题：{{theme}}

风格：{{style}}

画幅：{{aspect_ratio}}

要求：

{{requirements}}
```

变量缺失时：

1. 不允许静默忽略。
2. 必须抛出明确错误。
3. 必须写入任务日志。
4. 必须更新 `metadata.json`。

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
11. 不要凭空假定 API 参数，必须以当前项目依赖、SDK 或官方示例为准。

---

## 请求 JSON 规范

请求 JSON 保存位置：

```text
api/request.json
```

要求：

1. 保存完整业务请求参数。
2. 不保存 API Key。
3. 不保存 Authorization Header。
4. 必须记录模型名。
5. 必须记录最终提示词。
6. 必须记录图片尺寸、数量、输出格式等生成参数。
7. 如果包含输入图片路径，只记录项目内相对路径或脱敏路径。

---

## 响应 JSON 规范

响应 JSON 保存位置：

```text
api/response.json
```

要求：

1. 保存完整响应 JSON 或可排查问题的响应摘要。
2. 图片文件必须单独保存到 `images/`。
3. 如果响应中包含 base64 图片数据，可以根据实际体积选择：
   - 完整保存原始响应；
   - 或保存脱敏摘要，并确保图片已完整落盘。
4. 不得丢失错误排查所需的关键字段。
5. 不得写入敏感 Header 或密钥信息。

---

## 图片保存规范

生成图片统一保存到：

```text
images/
```

推荐命名：

```text
image_001.png
image_002.png
image_003.png
```

要求：

1. 不得覆盖已有图片。
2. 文件扩展名必须与实际输出格式一致。
3. 保存完成后必须将图片路径写入 `metadata.json`。
4. 保存失败必须写入任务日志与全局日志。

---

## 日志规范

日志系统必须接管所有接口请求与响应。

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
4. 使用提示词模板。
5. 使用提示词版本。
6. 输出目录。
7. 请求参数摘要。
8. 响应摘要。
9. 图片保存路径。
10. 请求耗时。
11. 总耗时。
12. 错误信息。
13. 异常堆栈。

日志中禁止出现：

1. API Key。
2. Token。
3. Secret。
4. Authorization Header。
5. 未脱敏环境变量。
6. 用户本地敏感绝对路径。

敏感信息必须脱敏，例如：

```text
OPENAI_API_KEY=sk-***abcd
```

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

## 命名规范

命名必须清晰、直观、可维护。

推荐：

```python
create_task_directory()
render_prompt_template()
save_response_json()
generate_image()
build_image_request()
save_image_file()
update_metadata()
```

避免：

```python
do()
handle()
process()
test1()
aaa()
tmp()
```

除非上下文非常明确，否则不要使用过短缩写。

---

## 注释规范

复杂逻辑必须写中文注释。

推荐注释内容：

1. 功能说明。
2. 输入输出。
3. 边界情况。
4. 复杂逻辑说明。

示例：

```python
# 功能说明：创建当前图片生成任务的独立输出目录
# 输入输出：输入任务名称，返回任务目录路径
# 边界情况：任务名称为空时使用时间戳兜底
# 复杂逻辑说明：目录已存在时自动追加随机后缀，避免覆盖历史结果
```

不要写重复代码表面含义的注释。

---

## 核心模块职责

### settings.py

职责：

1. 读取环境变量。
2. 读取默认配置。
3. 提供模型名、图片尺寸、输出目录等配置。
4. 检查 `OPENAI_API_KEY` 是否存在。
5. 不直接执行 API 请求。
6. 不直接处理提示词模板。
7. 不输出完整 API Key。

---

### image_client.py

职责：

1. 构造 GPT Image 2 API 请求。
2. 调用图片生成 API。
3. 返回结构化响应。
4. 不负责提示词模板渲染。
5. 不负责创建任务目录。
6. 不直接处理复杂业务流程。
7. 不在日志中输出敏感信息。

---

### prompt_engine.py

职责：

1. 读取 Markdown 提示词。
2. 读取模板。
3. 读取变量 JSON。
4. 执行变量替换。
5. 管理提示词版本。
6. 输出最终提示词。
7. 变量缺失时抛出明确错误。

---

### task_manager.py

职责：

1. 创建任务 ID。
2. 创建任务目录。
3. 创建 `images/`、`prompt/`、`api/`、`logs/` 等子目录。
4. 保存 `metadata.json`。
5. 维护任务状态。
6. 避免覆盖历史任务目录。

---

### generator.py

职责：

1. 接收用户输入。
2. 调用提示词引擎生成最终提示词。
3. 创建任务目录。
4. 保存原始提示词与最终提示词。
5. 调用图片 API。
6. 保存请求 JSON。
7. 保存响应 JSON。
8. 保存图片。
9. 写入日志。
10. 更新任务元信息。
11. 捕获异常并写入日志与 metadata。

---

### app_logger.py

职责：

1. 创建全局日志。
2. 创建任务日志。
3. 统一日志格式。
4. 敏感字段脱敏。
5. 记录异常堆栈。

---

### file_utils.py

职责：

1. 安全创建目录。
2. 安全写入文本。
3. 安全写入二进制文件。
4. 防止覆盖历史文件。
5. 写入前自动确保父目录存在。

---

### json_utils.py

职责：

1. 读取 JSON。
2. 保存 JSON。
3. 保证中文不被 ASCII 转义。
4. 格式化输出 JSON。
5. 处理 JSON 解析异常。

---

### image_utils.py

职责：

1. 解码 API 返回的图片数据。
2. 保存图片文件。
3. 根据输出格式决定扩展名。
4. 返回图片保存路径。
5. 响应格式不符合预期时抛出明确异常。

---

### time_utils.py

职责：

1. 获取北京时间。
2. 生成日期目录名。
3. 生成任务时间戳。
4. 计算耗时毫秒。

---

## 错误处理规范

以下情况必须处理并记录日志：

1. 配置缺失。
2. API Key 缺失。
3. 提示词文件不存在。
4. 变量文件不存在。
5. JSON 解析失败。
6. 模板变量缺失。
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
5. 随意重构无关代码。
6. 修改无关文件。
7. 大范围格式化项目。
8. 引入无必要的新框架。
9. 把临时测试代码留在主流程。
10. 吞掉异常不记录。
11. 只打印错误但不落盘。
12. 将所有逻辑堆在一个文件。
13. 让生成图片散落在项目根目录。
14. 破坏已有提示词格式。
15. 未经需求要求扩展为 Web 后台。
16. 未经需求要求扩展为 FastAPI 服务。
17. 未经需求要求引入数据库。
18. 未经需求要求引入复杂任务队列。
19. 凭空假定 GPT Image 2 API 参数。
20. 把完整响应中的敏感信息原样写入日志。

---

## 开发流程

每次开发必须按以下流程：

1. 阅读相关文件。
2. 判断影响范围。
3. 制定最小改动方案。
4. 修改必要文件。
5. 补充必要注释。
6. 检查语法。
7. 检查日志。
8. 检查输出目录。
9. 检查敏感信息是否脱敏。
10. 汇总修改结果。

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
8. 图片是否保存到独立任务目录。
9. 当前任务日志是否保存。
10. 异常堆栈是否保存。
11. `metadata.json` 是否更新。
12. 历史输出是否不会被覆盖。
13. 是否没有改动无关文件。
14. 是否没有引入无必要依赖。

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
