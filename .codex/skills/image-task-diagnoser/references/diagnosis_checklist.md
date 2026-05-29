# 失败任务诊断检查单

1. 先看 `metadata.json`
2. 再看 `api/response.json`
3. 再看 `logs/task.log`
4. 必要时再看 `api/request.json`
5. 认证问题先跑 `python -m src.api.auth_check`
6. 明确根因类别
7. 明确证据文件路径
8. 明确下一步动作
