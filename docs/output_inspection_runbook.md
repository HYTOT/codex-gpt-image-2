# 输出目录验收与复盘手册

本文档说明如何阅读一次任务的输出目录，适合成功验收、失败复盘和二次优化前的信息收集。

## 输出目录结构

标准任务目录：

```text
outputs/YYYY-MM-DD/YYYYMMDD_HHMMSS_task_xxxxx/
├── images/
├── prompt/
├── api/
├── logs/
├── inputs/
└── metadata.json
```

重点文件：

- `prompt/raw_prompt.md`
- `prompt/final_prompt.md`
- `api/request.json`
- `api/response.json`
- `logs/task.log`
- `metadata.json`

## 成功任务怎么验收

固定顺序：

1. 先看 `metadata.json`
2. 再看 `prompt/final_prompt.md`
3. 再看 `api/request.json`
4. 再看 `images/`
5. 最后看 `logs/task.log`

### 第一步：看 `metadata.json`

确认：

- `status` 是否为 `succeeded`
- `image_paths` 是否非空
- `source_task_prompt` 和 `source_raw_task` 是否指向预期任务
- `reference_image_paths`、`mask_image_path` 是否符合本次任务输入

### 第二步：看 `prompt/final_prompt.md`

确认：

- 最终发给模型的提示词是否就是你想要的版本
- 六段式是否真的把构图、主体、细节、用途、约束、优先级拆开写清
- 有没有把重要限制挤在单条里导致权重混乱

### 第三步：看 `api/request.json`

确认：

- `mode` 是否正确
- `size`、`n`、`output_format` 是否符合任务要求
- `quality` 和 `quality_source` 是否符合运行模式
- `reference_images` 与 `mask_image` 是否按预期传入
- `prompt_source_mode`、`source_task_prompt`、`source_raw_task` 是否记录正确

### 第四步：看 `images/`

确认：

- 图片是否真的落盘
- 数量是否与 `n` 一致
- 风格、人物、文字和约束是否达到任务目标

### 第五步：看 `logs/task.log`

确认：

- 请求摘要和响应摘要是否一致
- 是否有隐藏警告或异常重试迹象

## 失败任务怎么逆推

固定顺序：

1. 先看 `metadata.json`
2. 再看 `api/response.json`
3. 再看 `logs/task.log`
4. 再看 `api/request.json`
5. 最后回看 `prompt/` 和 `inputs/`

### `metadata.json` 负责定性

回答：

- 任务失败在什么阶段
- 失败摘要是什么
- 是否已经生成了请求和输入快照

### `api/response.json` 负责看平台回话

回答：

- 平台返回的是认证失败、参数失败，还是根本没有返回图片数据

### `logs/task.log` 负责补齐时序

回答：

- 哪一步最后成功
- 哪一步抛出异常
- 堆栈是在任务准备、请求发送还是图片保存阶段

### `api/request.json` 负责确认“是不是自己发错了”

重点看：

- `prompt`
- `size`
- `quality`
- `reference_images`
- `mask_image`
- `mode`

## 三个来源字段怎么看

### `prompt_source_mode`

当前应固定为：

- `structured_markdown`

作用：

- 说明这次任务来自结构化任务目录，而不是历史模板系统

### `source_task_prompt`

作用：

- 指向本次真正执行的 `task_prompt.md`
- 复盘时先看它，而不是先看当前工作区里后来改过的任务文件

### `source_raw_task`

作用：

- 指向原始需求归档文件
- 便于比较“原始需求”和“最终执行提示词”之间是否整理准确

## 参考图和 mask 快照怎么看

输入快照位置：

- `inputs/reference/`
- `inputs/mask/`

使用原则：

- 复盘时优先以输出目录里的快照为准，不以任务目录原文件为准
- 这样可以避免任务目录后续被替换或覆盖后，无法还原历史执行上下文

## 一次完整复盘至少回答什么

至少回答 5 个问题：

1. 本次任务是成功还是失败
2. 本次到底把什么提示词发给了模型
3. 本次到底带了哪些参考图和 mask
4. 本次平台返回了什么
5. 下一轮应该先改提示词、改素材、改参数，还是先查认证与网络

## 相关文档

- [认证与接口排查手册](./auth_and_api_troubleshooting.md)
- [任务提示词写作指南](./task_prompt_authoring_guide.md)
- [参考图策略说明](./reference_image_strategy.md)
