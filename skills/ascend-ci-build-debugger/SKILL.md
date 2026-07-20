---
name: ascend-ci-build-debugger
description: 提取 Ascend/pytorch CI Trigger 流水线 build 阶段失败日志，结合 pytorch/torch_npu 源码由 AI 分析根因并给出修复方案。当用户要求分析 CI build 失败、检查构建阶段报错、排查 pytorch_ci_trigger.yml 失败时触发。
---

# Ascend Build 阶段分析器

## 概述

本技能分析 `Ascend/pytorch` 仓库 `pytorch_ci_trigger.yml` Action 的 **build 阶段失败**。

主要分析目标是 `forward / build / pytorch_and_torch-npu_build` job 的失败（阻塞性问题，需最高优先级解决）。同时也覆盖 build 前置步骤的失败（如 `forward / build / fetch` 等），这类失败通常由网络问题或 GitHub Actions 自身问题导致，可能不涉及 pytorch 源码或 PR 引入，但同样需要输出分析报告和通知。

工作流程分三步：

1. **脚本提取** — 用 `gh run view --log-failed` 下载失败 job 的完整日志
2. **源码交叉引用 + git 历史追溯** — 利用本地 clone 的 pytorch / torch_npu 源码定位出错代码，并通过 `gh api` 追溯引入问题的 commit 和 PR
3. **AI 分析** — 逐错误分析根因，输出结构化报告

## 工作流程

### 第零步（必须）：确认输入参数

技能被触发后，需从用户消息或环境变量中获取以下参数：

| 参数 | 环境变量 | 说明 |
|------|----------|------|
| run_id | `CI_RUN_ID` | GitHub Actions Run ID（数字或 URL） |
| pytorch 源码路径 | `PYTORCH_SRC` | 本地 pytorch 源码目录（`--depth=1` clone） |
| torch_npu 源码路径 | `TORCH_NPU_SRC` | 本地 Ascend/pytorch 源码目录（`--depth=1` clone） |
| 日志输出目录 | `LOG_DIR` | 日志和报告的输出目录（默认 `/tmp/ci-analysis`） |

如果参数缺失，向用户索要。

### 第一步：运行提取脚本

```bash
python3 <skill-dir>/scripts/extract_failure_logs.py <run-id> --output <LOG_DIR>
```

脚本自动完成：

1. 调用 `gh run view <run-id> --repo Ascend/pytorch --log-failed` 获取失败 job 日志
2. 解析日志，按 job 分割，提取每个失败 job 的：
   - job 名称
   - 失败 step 名称
   - 关键错误行（`##[error]`、`error:`、`Error:`、`FAILED` 等）
   - 完整错误上下文（错误行前后各 50 行）
3. 输出结构化 JSON 到 `<LOG_DIR>/failures.json`

### 第二步：AI 逐错误分析

对 `failures.json` 中每个失败 job，AI 需要：

1. **阅读完整错误日志** — 理解失败发生的阶段（编译/链接/安装/配置）
2. **提取关键错误行** — 找出编译器报错、cmake 报错、依赖缺失等核心信息
3. **源码交叉引用** — 用 `grep`/`glob`/`read` 工具在 pytorch 源码（`$PYTORCH_SRC`）和 torch_npu 源码（`$TORCH_NPU_SRC`）中搜索：
   - 出错的源文件和行号
   - 相关的 CMakeLists.txt / setup.py 配置
   - 相关的 patch 文件（torch_npu 中的 `*.patch`）
4. **分析根因** — 判断失败的根本原因
5. **给出修复方案** — 具体可操作的修复步骤（含文件路径和改动内容）
6. **追溯引入问题的 PR** — 注意：源码为 `--depth=1` 浅克隆，`git log`/`git blame` 无历史，需通过 `gh api` 查询：
   - 定位到出错的源文件后，查询该文件的最近提交历史：
     ```bash
     gh api "repos/pytorch/pytorch/commits?path=<文件路径>&per_page=10" --jq '.[] | {sha,message:.commit.message[:80],date:.commit.committer.date,author:.author.login}'
     ```
   - 或对 torch_npu 仓库：
     ```bash
     gh api "repos/Ascend/pytorch/commits?path=<文件路径>&per_page=10" --jq '.[] | {sha,message:.commit.message[:80],date:.commit.committer.date,author:.author.login}'
     ```
   - 根据提交信息和错误类型，判断哪个 commit 最可能引入了问题
   - 查询该 commit 关联的 PR：
     ```bash
     gh api "repos/<owner>/<repo>/commits/<sha>/pulls" --jq '.[] | {number,title,url,merged_at,user:.user.login}'
     ```
   - 如果是网络/基础设施类失败（无源码变更），注明"不适用 — 基础设施问题"
   - 如果无法确定具体 PR，在报告中注明"无法确定"并说明原因

### 第三步：输出分析报告

将分析结果写入 `<LOG_DIR>/report.md`，格式如下：

```markdown
---
run_id: <run-id>
run_name: <run_name>
run_url: https://github.com/Ascend/pytorch/actions/runs/<run-id>
analyzed_at: <ISO 8601 时间>
fingerprint: <失败指纹，由 check_duplicate.py 计算，从环境变量 FINGERPRINT 获取>
failed_jobs:
  - <job 1 名称>
  - <job 2 名称>
---

# CI Build 失败分析报告

## 运行信息

| 字段 | 值 |
|------|-----|
| Run ID | <run-id> |
| Run Name | <run_name> |
| 触发仓库 | <upstream_repo> |
| 失败时间 | <created_at> |
| 运行链接 | https://github.com/Ascend/pytorch/actions/runs/<run-id> |

## 失败概览

| # | 失败 Job | 失败 Step | 错误类型 |
|---|----------|-----------|----------|
| 1 | <job> | <step> | <类型> |

## 详细分析

### 失败 1: <job 名称>

**失败 Step**: <step 名称>

**关键错误日志**:
```
<核心错误行>
```

**根因分析**:
<详细分析，含源码文件:行号引用>

**引入问题的 PR**（AI 基于 git 历史分析，非触发 PR）:
- PR 链接: <PR URL 或"无法确定">
- PR 标题: <标题>
- 合入时间: <mergedAt>
- 作者: <author>
- 引入 commit: <commit SHA>
- 判断依据: <为什么认为是这个 PR 引入的>

**修复方案**:
<具体修复步骤>

**相关源码**:
- `pytorch/<path>:<line>`
- `torch_npu/<path>:<line>`
```
