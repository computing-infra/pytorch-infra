---
name: ascend-ci-build-debugger
description: 提取 Ascend/pytorch CI Trigger 流水线 build 阶段失败日志，结合 pytorch/torch_npu 源码由 AI 分析根因并给出修复方案。当用户要求分析 CI build 失败、检查构建阶段报错、排查 pytorch_ci_trigger.yml 失败时触发。
---

# Ascend Build 阶段分析器

## 概述

本技能分析 `Ascend/pytorch` 仓库 `pytorch_ci_trigger.yml` Action 的 **build 阶段失败**。

工作流程分四步：

1. **脚本提取** — 用 `gh run view --log-failed` 下载失败 job 的完整日志
2. **获取触发 PR 信息** — 从 run_name 提取 PR 编号，用 `gh pr view` 获取 PR 链接、合入时间等
3. **源码交叉引用** — 利用本地 clone 的 pytorch / torch_npu 源码定位出错代码
4. **AI 分析** — 逐错误分析根因，输出结构化报告

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

### 第二步：获取触发 PR 信息

从 `failures.json` 的 `run_name` 中提取 PR 编号（格式 `PR #189672 (closed)`），用 `gh` 获取 PR 详情：

```bash
gh pr view <PR编号> --repo pytorch/pytorch --json url,mergedAt,title,author
```

获取以下信息：
- PR 链接（`url`）
- 合入时间（`mergedAt`）
- PR 标题（`title`）
- 作者（`author.login`）

### 第三步：AI 逐错误分析

对 `failures.json` 中每个失败 job，AI 需要：

1. **阅读完整错误日志** — 理解失败发生的阶段（编译/链接/安装/配置）
2. **提取关键错误行** — 找出编译器报错、cmake 报错、依赖缺失等核心信息
3. **源码交叉引用** — 用 `grep`/`glob`/`read` 工具在 pytorch 源码（`$PYTORCH_SRC`）和 torch_npu 源码（`$TORCH_NPU_SRC`）中搜索：
   - 出错的源文件和行号
   - 相关的 CMakeLists.txt / setup.py 配置
   - 相关的 patch 文件（torch_npu 中的 `*.patch`）
4. **分析根因** — 判断失败的根本原因
5. **给出修复方案** — 具体可操作的修复步骤（含文件路径和改动内容）

### 第四步：输出分析报告

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
| 引入问题的 PR | [<PR标题>](<PR链接>) |
| PR 合入时间 | <mergedAt> |
| PR 作者 | <author> |

## 失败概览

| # | 失败 Job | 失败 Step | 错误类型 | 优先级 |
|---|----------|-----------|----------|--------|
| 1 | <job> | <step> | <类型> | P0 |

## 详细分析

### 失败 1: <job 名称>

**失败 Step**: <step 名称>

**关键错误日志**:
```
<核心错误行>
```

**根因分析**:
<详细分析，含源码文件:行号引用>

**修复方案**:
<具体修复步骤>

**相关源码**:
- `pytorch/<path>:<line>`
- `torch_npu/<path>:<line>`
```

## 优先级定义

| 优先级 | 含义 |
|--------|------|
| P0 | 阻塞性问题，所有 PR 都会失败（如 CANN 版本、GCC 配置） |
| P1 | 高优先级，需尽快修复（如 pytorch API 变更、patch 失败） |
| P2 | 中等优先级，可排期（如偶发的依赖下载失败） |
| P3 | 低优先级 / 基础设施问题（如磁盘空间、OOM） |
