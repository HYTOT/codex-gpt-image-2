# codex-gpt-image-2

`codex-gpt-image-2` 是一个基于 Python 的 GPT Image 2 图片生成任务工程，当前只支持六段式结构化任务模式。每次任务都以 `tasks/<任务名>/` 目录为单位组织原始需求、最终提示词、参考图和输出结果。

## 当前模式

- 运行时只接受结构化任务目录：`task.json + raw_task.md + task_prompt.md + 可选参考图/mask`
- 不再支持 `prompt_name`、`prompt_version`、`variables_file`、`prompt_source`
- 不再读取 `prompts/templates/`、`prompts/versions/`、`prompts/variables/`

## 项目结构

```text
codex-gpt-image-2/
├── AGENTS.md
├── README.md
├── docs/
├── tasks/
├── requirements.txt
├── .env.example
├── main.py
├── configs/
│   ├── config.example.json
│   ├── task.example.json
│   └── task.json
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

## 环境变量

先复制 `.env.example` 为 `.env`，然后至少配置：

```env
OPENAI_API_KEY=
IMAGE_MODEL=gpt-image-2
RUN_MODE=production
OPENAI_IMAGE_QUALITY=
DEFAULT_IMAGE_SIZE=3840x2160
DEFAULT_IMAGE_FORMAT=png
DEFAULT_IMAGE_COUNT=1
```

说明：

- `IMAGE_MODEL` 只允许使用 `gpt-image-2`
- `OPENAI_API_KEY` 不允许写入代码或日志
- `RUN_MODE=test` 时始终强制发送 `quality=low`
- 非 `test` 模式下，未设置 `OPENAI_IMAGE_QUALITY` 时默认发送 `quality=high`
- `OPENAI_IMAGE_QUALITY=hd` 仅适用于文本生图，不适用于参考图编辑

## 安装

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

验证依赖：

```bash
python -c "import openai; from openai import OpenAI; from dotenv import load_dotenv; print(openai.__version__)"
```

## 任务目录规范

每个新任务推荐放在：

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

`task.json` 当前仅支持以下字段：

```json
{
  "reference_images": [],
  "mask_image": "",
  "image_size": "3840x2160",
  "image_format": "png",
  "image_count": 1
}
```

字段说明：

- `reference_images`：参考图路径数组，相对于当前任务目录
- `mask_image`：可选 mask 路径，相对于当前任务目录
- `image_size`：本次任务尺寸
- `image_format`：输出格式
- `image_count`：输出张数

入口配置 `configs/task.json` 只保留任务指针，例如：

```json
{
  "task_file": "tasks/ZhangXiaoHuaChefPlacardDataOps/task.json"
}
```

## 六段式提示词规范

`raw_task.md` 用于归档原始需求，不直接发给模型。

`task_prompt.md` 才是最终执行提示词。新增任务时，Codex 必须在创建阶段直接写出合规六段式内容，而不是依赖运行时兜底修正：

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

规则：

- 每个 `##` 下必须有 3 到 5 个 `-` 条目
- 单条 `-` 必须是完整中文提示句，长度适中、信息密度高，避免把多个维度塞进一条冗长散文句
- 每个任务默认视为独立新任务
- 不允许出现 `弃用 / 改用 / 不再 / 上一轮 / 上个任务 / 上一版 / 之前那版`
- 创建任务后先自查 `task_prompt.md` 是否符合六段式，并确认每段覆盖不同维度的信息点，再更新 `configs/task.json`

运行时当前只做最小检查：

- `raw_task.md` 必须存在且非空
- `task_prompt.md` 必须存在且非空
- 运行时不再过滤标题顺序、条目数量或禁用话术，结构质量由建任务阶段保证

## 运行

```bash
python main.py
```

程序会优先读取：

- `configs/task.json`
- 若不存在，则回退读取 `configs/task.example.json`

## 认证排查

如果 `python main.py` 返回 `401 invalid_api_key`，先运行独立认证检查：

```bash
python -m src.api.auth_check
```

说明：

- 这个检查会直接验证当前 `.env` 中的 `OPENAI_API_KEY` 是否被 OpenAI 平台接受
- 它不依赖当前任务目录，也不走图片生成主流程
- 若这里仍失败，问题基本可收敛为 key 本身无效、已撤销、项目不匹配，或账号没有 Platform API 权限

## 输出目录

每次任务都会创建独立目录：

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

- `prompt/raw_prompt.md`
- `prompt/final_prompt.md`
- `api/request.json`
- `api/response.json`
- `logs/task.log`
- `metadata.json`
- `inputs/reference/` 中的参考图快照
- `inputs/mask/` 中的 mask 快照

说明：

- `metadata.json` 和 `request.json` 会记录 `prompt_source_mode=structured_markdown`、`source_task_prompt`、`source_raw_task`

## 日志与安全

- 全局日志：`logs/app.log`
- 任务日志：`outputs/.../logs/task.log`
- 日志会记录任务开始、请求摘要、响应摘要、图片保存路径、耗时与异常堆栈
- 请求 JSON 与响应 JSON 不保存 API Key 或 Authorization Header
- 不覆盖历史输出目录，不删除历史任务结果

## 测试

```bash
python -m pytest tests/test_task_prompt_modes.py
python -m compileall src tests main.py
```

## 参考文档

- 详细操作手册见：[docs/image_task_guide.md](docs/image_task_guide.md)
- 协作与开发约定见：[AGENTS.md](AGENTS.md)
