# 参考图生图操作手册

本文档说明当前工程中唯一支持的任务方式：六段式结构化任务模式。

## 适用场景

- 纯文本生图：`reference_images=[]`
- 单张参考图生图：`reference_images` 里只有 1 张图
- 多张参考图生图：`reference_images` 里有 2 张及以上图片
- 多参考图 + mask 编辑：`reference_images` 非空且 `mask_image` 非空

## 标准目录

每个任务都放在：

```text
tasks/<任务名>/
```

目录内至少包含：

```text
task.json
raw_task.md
task_prompt.md
```

如有需要，再补充：

```text
reference_images/
mask/
```

## 执行前准备

开始前请确认：

- 已在 `.env` 中配置 `OPENAI_API_KEY`
- 所有路径都使用项目内相对路径
- 参考图和 mask 仅支持 `.png`、`.jpg`、`.jpeg`、`.webp`
- 新任务默认视为独立任务，不写跨任务修订语气

## 六段式提示词

`raw_task.md` 用于归档原始需求，不直接发给模型。

`task_prompt.md` 必须固定为：

```md
## 场景
- ...

## 主体
- ...

## 关键细节
- ...

## 用途
- ...

## 约束
- ...

## 特别要求
- ...
```

创建任务时的要求：

- 每个标题下必须有 1 到 3 个 `-`
- 标题顺序不能变
- 条目可以是中长句，但不要写成散文
- 不允许出现 `弃用 / 改用 / 不再 / 上一轮 / 上个任务 / 上一版 / 之前那版`
- 先自查 `task_prompt.md` 写对，再把任务挂到 `configs/task.json`

运行时当前只做最小检查：

- `raw_task.md` 必须存在且非空
- `task_prompt.md` 必须存在且非空
- 结构问题不会在运行时被硬拦截，若出图质量异常，先回看任务创建阶段写出的 `task_prompt.md`

## 配置字段

`task.json` 当前仅支持：

```json
{
  "reference_images": [],
  "mask_image": "",
  "image_size": "3840x2160",
  "image_format": "png",
  "image_count": 1
}
```

字段约定：

- `reference_images`：参考图路径数组，相对于当前任务目录
- `mask_image`：可选 mask 路径，相对于当前任务目录
- `image_size`：本次任务尺寸
- `image_format`：输出格式
- `image_count`：输出张数

以下旧字段已经弃用，出现在 `task.json` 中会直接报错：

- `prompt_name`
- `prompt_version`
- `variables_file`
- `prompt_source`

## 入口配置

`configs/task.json` 只保留任务指针：

```json
{
  "task_file": "tasks/<任务名>/task.json"
}
```

程序会优先读取 `configs/task.json`，若不存在，则回退读取 `configs/task.example.json`。

## 标准操作步骤

1. 新建 `tasks/<任务名>/`
2. 写 `raw_task.md`，归档本次任务的原始需求
3. 把需求整理成六段式 `task_prompt.md`
4. 先人工或由 Codex 自查六段式结构与语气是否合规
5. 准备参考图和可选 mask
6. 写当前任务的 `task.json`
7. 修改 `configs/task.json` 中的 `task_file`
8. 执行 `python main.py`
9. 检查输出目录中的提示词、请求摘要、响应摘要、日志和图片

## 最小示例

`configs/task.json`：

```json
{
  "task_file": "tasks/CiHuaQianQiu/task.json"
}
```

`tasks/CiHuaQianQiu/task.json`：

```json
{
  "reference_images": [
    "reference_images/reference_01_main.png",
    "reference_images/reference_02_detail.png"
  ],
  "mask_image": "",
  "image_size": "3840x2160",
  "image_format": "png",
  "image_count": 1
}
```

## 输出结果如何验收

每次任务都会写入独立目录：

```text
outputs/YYYY-MM-DD/YYYYMMDD_HHMMSS_task_xxxxx/
```

建议按以下顺序检查：

1. `prompt/raw_prompt.md`：确认原始需求归档是否正确
2. `prompt/final_prompt.md`：确认六段式最终提示词是否符合预期
3. `api/request.json`：确认模型、尺寸、质量、参考图路径顺序、mask 路径
4. `api/response.json`：确认接口是否返回图像数据或错误摘要
5. `images/`：确认图片是否成功落盘
6. `metadata.json`：确认 `status`、`image_paths`、`reference_image_paths`、`mask_image_path`、`source_task_prompt`、`source_raw_task`
7. `logs/task.log`：确认请求摘要、响应摘要、异常堆栈

## 常见失败排查

### 路径错误

典型现象：

- `raw_task.md 对应文件不存在`
- `task_prompt.md 对应文件不存在`
- `reference_images[0] 对应文件不存在`
- `mask_image 对应文件不存在`

处理方式：

- 确认文件已放在项目目录内
- 确认 `task.json` 中填写的是相对当前任务目录的路径
- 不要填写盘符绝对路径

### 图片后缀不支持

典型现象：

- `reference_images[0] 必须是图片文件`
- `mask_image 必须是图片文件`

处理方式：

- 改用 `.png`、`.jpg`、`.jpeg` 或 `.webp`

### 任务提示词缺失或为空

典型现象：

- `task_prompt.md 对应文件不存在`
- `task_prompt.md 不能为空`
- `raw_task.md 不能为空`

处理方式：

- 先补齐缺失文件，确保任务目录结构完整
- 确认两个 Markdown 文件都有实际内容，而不是空白占位
- 如果结构写错导致出图偏差，回到任务创建阶段重写 `task_prompt.md`，而不是等待运行时拦截

### 旧字段未迁移干净

典型现象：

- `结构化任务配置存在已弃用字段`

处理方式：

- 删除 `prompt_name`、`prompt_version`、`variables_file`、`prompt_source`
- 保留当前结构化任务 schema 的 5 个字段

### API 请求失败或响应无图像数据

典型现象：

- `api/response.json` 中只有错误摘要
- `logs/task.log` 中出现接口异常或响应格式异常

处理方式：

- 先检查 `final_prompt.md` 与 `api/request.json`
- 再检查 API Key、网络和模型权限
- 如任务失败，优先以 `metadata.json` 的 `status` 与 `error` 为准

## 质量规则

- 非 `test` 模式：未显式设置 `OPENAI_IMAGE_QUALITY` 时默认 `high`
- `RUN_MODE=test`：始终强制 `quality=low`

## 协作约定

- 每次新需求先建新的 `tasks/<任务名>/`
- 不直接覆盖历史输出目录中的任何文件
- 原始需求放在 `raw_task.md`，最终执行提示词放在 `task_prompt.md`
- 参考图和 mask 只在当前任务目录内维护，避免多人共用临时素材
- 如果要复现某次任务，优先查看该任务目录中的 `raw_task.md`、`task_prompt.md` 和对应输出目录中的 `prompt/`、`api/`、`metadata.json`、`logs/task.log`
