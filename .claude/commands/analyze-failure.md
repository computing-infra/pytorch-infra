分析最新一次失败的 GitHub Actions CI 构建，输出结构化的根本原因报告。

## 执行步骤

1. 用 `gh run list --repo kerer-ai/pytorch-npu --limit 5` 列出最近的 workflow 运行记录
2. 找到最近一次 status 为 `failure` 的 run，记录其 run ID
3. 用 `gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed` 拉取失败步骤的完整日志
4. 过滤出关键错误行（error、fatal、Traceback、make[*]: Error 等）
5. 分析错误根因，按以下结构输出报告：

```
## 失败 Run 信息
- Run ID：
- 触发时间：
- 失败步骤：

## 错误摘要
（列出 3-5 条最关键的编译/运行错误）

## 根本原因
（说明是哪个文件、哪个 API 发生了什么变化导致失败）

## 受影响范围
（涉及的文件、类、函数）

## 建议修复方向
（简要描述如何修复）
```

6. 同时输出以下信息供后续 skill 使用：
   - 受影响的源文件路径（相对于 Ascend/pytorch 根目录）
   - PyTorch nightly 版本号（从日志中提取）
   - Ascend/pytorch commit hash（从日志中提取）
