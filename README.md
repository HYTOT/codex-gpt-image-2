# codex-gpt-image-2

`codex-gpt-image-2` 是一个基于 Python 的 GPT Image 2 图片生成提示词工程项目，用于管理 Markdown 提示词模板、提示词版本、变量替换，以及图片生成任务的完整落盘。

## 项目结构

```text
codex-gpt-image-2/
├── AGENTS.md
├── README.md
├── docs/
├── examples/
├── requirements.txt
├── .env.example
├── main.py
├── configs/
│   ├── config.example.json
│   ├── prompt_versions.json
│   └── task.example.json
├── prompts/
│   ├── templates/
│   ├── versions/
│   └── variables/
├── src/
│   ├── api/
│   ├── config/
│   ├── core/
│   ├── logger/
│   └── utils/
├── outputs/
├── logs/
└── tests/
```

## 环境变量配置

先复制 `.env.example` 为 `.env`，然后至少配置：

```env
OPENAI_API_KEY=
IMAGE_MODEL=gpt-image-2
DEFAULT_IMAGE_SIZE=3840x2160
DEFAULT_IMAGE_FORMAT=png
DEFAULT_IMAGE_COUNT=1
```

说明：

- `IMAGE_MODEL` 只允许使用 `gpt-image-2`。
- `OPENAI_API_KEY` 不允许写入代码或日志。
- 默认尺寸已统一为 4K 16:9 的 `3840x2160`。

## 环境安装与升级

建议按以下顺序安装或升级环境：

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt
```

当前工程依赖 OpenAI Python SDK 来承接 GPT Image 2 的参考图输入能力。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行方式

```bash
python main.py
```

程序会优先读取：

- `configs/task.json`
- 如果不存在，则回退读取 `configs/task.example.json`

## 多参考图快速开始

多参考图需求仍然使用同一个入口：

1. 复制一份 `configs/task.multi-reference.example.json` 或 `configs/task.multi-reference-mask.example.json` 为 `configs/task.json`
2. 把 `reference_images` 按优先级填写为 0~N 个项目内相对路径
3. 需要局部编辑时再填写 `mask_image`
4. 执行 `python main.py`

详细操作步骤、排查方式和协作约定见：[docs/参考图生图操作手册.md](docs/参考图生图操作手册.md)

## 任务配置说明

任务配置示例：

```json
{
  "prompt_name": "default",
  "prompt_version": "",
  "variables_file": "prompts/variables/example.json",
  "reference_images": [],
  "mask_image": "",
  "image_size": "3840x2160",
  "image_format": "png",
  "image_count": 1
}
```

字段说明：

- `prompt_name`：提示词名称。
- `prompt_version`：可选，不填时读取版本索引中的 `latest`。
- `variables_file`：变量 JSON 文件，相对于项目根目录。
- `reference_images`：参考图路径数组，为空时执行文本生图。
- `mask_image`：可选 mask 路径；当 `reference_images` 非空且 `mask_image` 非空时，执行编辑模式。
- `image_size`：本次任务图片尺寸，默认 `3840x2160`。
- `image_format`：输出格式，默认 `png`。
- `image_count`：输出图片数量，默认 `1`。

协作建议：

- `reference_images` 支持 0~N 张图片，数组顺序即上传顺序。
- 建议将主体角色、主体风格或主构图参考放在数组第 1 位。
- 示例配置中的 `examples/reference_images/` 仅为占位素材，用于演示路径写法与配置结构。

## 输出目录说明

每次生成任务都会创建独立目录：

```text
outputs/YYYY-MM-DD/YYYYMMDD_HHMMSS_task_xxxxx/
```

任务目录内包含：

```text
images/
prompt/
api/
logs/
inputs/
metadata.json
```

其中会保存：

- 生成图片
- `prompt/raw_prompt.md`
- `prompt/final_prompt.md`
- `prompt/variables.json`
- `api/request.json`
- `api/response.json`
- `logs/task.log`
- `metadata.json`
- `inputs/reference/` 中的参考图快照
- `inputs/mask/` 中的 mask 快照

## 日志说明

- 全局日志：`logs/app.log`
- 任务日志：`outputs/.../logs/task.log`

日志会记录任务开始、请求摘要、响应摘要、图片保存路径、耗时与异常堆栈，并对密钥与敏感路径做脱敏处理。

## 安全注意事项

- 禁止硬编码 `OPENAI_API_KEY`
- 禁止在日志中输出完整 API Key、Token、Secret、Authorization Header
- 禁止覆盖已有输出文件
- 禁止删除历史任务目录
- 请求 JSON 与响应 JSON 不保存敏感头信息
- 参考图与 mask 只记录任务目录内相对路径

## 后续扩展方向

- 扩展更多提示词模板与版本
- 增加 CLI 参数支持
- 增加测试用例
- 在保持现有结构的前提下扩展为 FastAPI 或 Web 管理后台
