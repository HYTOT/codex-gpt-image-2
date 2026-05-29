# 认证与接口排查手册

本文档只处理“为什么这次任务没跑通”，不重复 README 里的完整安装说明。

## 先看哪里

排查顺序固定为：

1. 先看 `outputs/.../metadata.json`
2. 再看 `outputs/.../api/response.json`
3. 再看 `outputs/.../logs/task.log`
4. 必要时再看 `outputs/.../api/request.json`
5. 如果怀疑是认证问题，再运行 `python -m src.api.auth_check`

## 认证检查命令

独立认证检查命令：

```bash
python -m src.api.auth_check
```

这个命令的作用：

- 直接验证当前 `.env` 中的 `OPENAI_API_KEY` 是否被 OpenAI 平台接受
- 不依赖 `tasks/` 目录，不走图片生成主流程
- 适合快速区分“是 key 问题”还是“是任务/请求问题”

## `auth_check` 输出含义

### `status=ok`

含义：

- 当前 API Key 被平台接受
- 认证链路本身正常

下一步：

- 回到任务输出目录继续查 `request.json`、`response.json` 和 `task.log`

### `status=invalid_api_key`

含义：

- OpenAI 平台拒绝了当前 key
- 常见原因是 key 已撤销、来自错误平台、项目不匹配或账号没有 Platform API 权限

下一步：

- 到 `https://platform.openai.com/api-keys` 重新生成 key
- 确认 key 来自 OpenAI Platform，而不是 ChatGPT 网页、第三方代理或 Azure OpenAI
- 替换 `.env` 后重新运行 `python -m src.api.auth_check`

### `status=network_error`

含义：

- 本地到 OpenAI 平台的网络没有打通

下一步：

- 检查网络、代理、防火墙和企业出口策略
- 确认不是临时 DNS 或 TLS 问题

### `status=unexpected_error`

含义：

- 不是常见认证或连通性错误

下一步：

- 直接查看 `task.log` 和终端堆栈
- 同时确认 SDK 版本和当前调用签名是否还匹配

## 常见接口失败归类

### 401 `invalid_api_key`

证据位置：

- `api/response.json` 里的错误摘要
- `metadata.json` 的 `error`
- `logs/task.log` 里的异常堆栈

判断原则：

- 先跑 `python -m src.api.auth_check`
- 如果独立检查也失败，优先认定为 key 或平台权限问题，而不是任务提示词问题

### SDK 兼容性异常

典型特征：

- 错误信息里出现“当前 OpenAI SDK 与 gpt-image-2 接口能力不匹配”

证据位置：

- `src/api/image_client.py`
- `task.log` 异常堆栈

下一步：

- 检查 `requirements.txt`
- 运行 README 里的依赖验证命令，确认 `openai` 版本与当前代码一致

### 请求参数问题

典型特征：

- 认证通过，但接口返回参数错误或业务错误

先看：

- `api/request.json`
- `task.json`
- `task_prompt.md`

重点检查：

- `mode`
- `size`
- `output_format`
- `quality` 与 `quality_source`
- `reference_images` 和 `mask_image`
- `prompt_source_mode`、`source_task_prompt`、`source_raw_task`

## 与运行模式有关的排查点

### `RUN_MODE=test`

已知行为：

- 请求会被强制降到 `quality=low`

排查方式：

- 在 `api/request.json` 里看 `quality`
- 在 `api/request.json` 里看 `quality_source`，应为 `test_forced_low`

### 非 `test` 模式

已知行为：

- 未显式设置 `OPENAI_IMAGE_QUALITY` 时默认 `high`

排查方式：

- 看 `api/request.json` 里的 `quality` 和 `quality_source`

## 什么时候看哪个文件

### 看 `metadata.json`

适合回答：

- 任务最终成功还是失败
- 当前报错摘要是什么
- 这次跑的是哪个任务目录
- 参考图快照和 mask 快照落盘了没有

### 看 `api/request.json`

适合回答：

- 本次到底给接口发了什么业务参数
- 是 `generate` 还是 `edit`
- 提示词、尺寸、质量、参考图路径是否符合预期

### 看 `api/response.json`

适合回答：

- 平台到底返回了图片数据还是错误摘要
- 如果失败，返回的是认证失败、参数失败还是别的业务错误

### 看 `logs/task.log`

适合回答：

- 出错前后完整时序是什么
- 请求摘要、响应摘要、堆栈细节是什么
- 问题发生在“任务准备”“API 请求”“图片保存”哪个阶段

## 相关文档

- [输出验收手册](./output_inspection_runbook.md)
- [测试与 smoke check 清单](./testing_and_smoke_checks.md)
- [参考图生图操作手册](./image_task_guide.md)
