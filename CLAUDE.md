# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

本仓库用于**每日集成验证** [Ascend/pytorch](https://gitcode.com/Ascend/pytorch.git) 与 PyTorch nightly 版本的编译兼容性，以及**代码静态扫描**。

### 核心定位
- **每日集成**：自动拉取 PyTorch nightly 和 Ascend/pytorch 最新代码进行编译验证
- **代码扫描**：定期对 Ascend/pytorch 进行代码静态分析
- **问题追踪**：CI 失败或 lint 检查发现问题时，创建 issue 记录
- **修复建议**：输出根本原因分析和修复建议，但**不需要直接修复或生成 patch**

### 工作边界
- ✅ 分析错误日志、定位根本原因
- ✅ 生成结构化 issue 文档
- ✅ 提供修复建议和方向
- ❌ 不直接修改 Ascend/pytorch 源码
- ❌ 不生成或提交 patch 文件

## 常用命令

### CI 操作
```bash
# 查看最近的 CI 运行记录
gh run list --repo computing-infra/pytorch-infra --limit 5

# 手动触发构建
gh workflow run nightly-build.yml --repo computing-infra/pytorch-infra

# 手动触发 lint 检查
gh workflow run lint.yml --repo computing-infra/pytorch-infra

# 查看失败运行的日志
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed
```

### 本地 Lint 测试
```bash
# 运行 lint 检查（克隆 Ascend/pytorch 到 /tmp/ascend_pytorch_lint）
.github/scripts/lint-runner.sh

# 运行 lint 检查（指定已有目录）
.github/scripts/lint-runner.sh /path/to/ascend_pytorch

# 自动修复可修复的问题
.github/scripts/lint-fix.sh /path/to/ascend_pytorch
```

### 本地 Ascend/pytorch 源码分析

源码路径：`.tmp/ascend_pytorch`

**按 CI 构建 commit 切换源码：**

```bash
# 1. 从 CI 日志提取 commit id
gh run view <run_id> --repo computing-infra/pytorch-infra --log 2>&1 \
  | grep -E "Ascend/pytorch commit:" | head -1

# 2. 切换到对应 commit（源码已存在）
if [ -d ".tmp/ascend_pytorch" ]; then
  cd .tmp/ascend_pytorch
  git fetch --depth=1 origin ${ASCEND_COMMIT}
  git checkout ${ASCEND_COMMIT}
  cd -
# 或克隆新仓库（源码不存在）
else
  git clone --depth=1 https://gitcode.com/Ascend/pytorch.git .tmp/ascend_pytorch
  cd .tmp/ascend_pytorch
  git fetch --depth=1 origin ${ASCEND_COMMIT}
  git checkout ${ASCEND_COMMIT}
  cd -
fi
```

**说明**：CI 每次构建使用特定 commit，分析时必须切换到对应版本才能准确定位问题。

### PyTorch Nightly 头文件
```bash
# API 对比时使用的头文件路径
/usr/local/lib/python3.12/dist-packages/torch/include/
```

## 架构

### Workflow: `.github/workflows/nightly-build.yml`
- **触发方式**：每日 UTC 21:00（北京时间 05:00）自动触发，或通过 `workflow_dispatch` 手动触发
- **运行环境**：`ubuntu-22.04`，Python 3.11
- **构建流程**：
  1. 安装 PyTorch nightly（CPU 版）
  2. 克隆 Ascend/pytorch（含子模块）
  3. 执行 `python setup.py build bdist_wheel` 构建 wheel
  4. 上传构建产物（构建日志，成功时上传 wheel）

### Issue 追踪 (`issues/`)
- 格式：`YYYY-MM-DD-NNN-<模块描述>.md`
- 记录根本原因、受影响文件、修复建议

### Workflow: `.github/workflows/lint.yml`
- **触发方式**：每周一 UTC 10:00（北京时间 18:00）自动触发，或通过 `workflow_dispatch` 手动触发
- **运行环境**：`ubuntu-22.04`，Python 3.11
- **检查流程**：
  1. 克隆 Ascend/pytorch 最新代码
  2. 应用 lint 配置文件（`.lintrunner.toml`, `.clang-format`）
  3. 使用 lintrunner 执行代码静态扫描
  4. 生成报告并创建 issue（如发现问题）

### Linter 配置 (`lint-config/`)
- `.lintrunner.toml`：lintrunner 配置，定义检查规则
- `.clang-format`：C++ 代码格式化配置

### Linter 工具 (`lint-tools/adapters/`)
从 PyTorch 复制的 linter 适配器脚本：
- `flake8_linter.py`：Python PEP8 检查
- `clangformat_linter.py`：C++ 代码格式化检查
- `newlines_linter.py`：换行符检查
- `grep_linter.py`：通用模式匹配检查

## Slash 命令

| 命令 | 用途 |
|------|------|
| `/analyze-failure` | 分析最新 CI 构建：失败时创建 issue，成功时关闭已修复的 issue |
| `/sync-issues` | 将 GitHub issue 同步到 GitCode（`Ascend/pytorch`） |
| `/scheduled-ci-analysis` | 创建每日定时 CI 分析任务（北京时间 08:00） |

### 典型工作流
```
/analyze-failure
    │
    ├─ ❌ 构建失败 → 分析原因 → 创建 GitHub issue → /sync-issues → GitCode issue
    │
    └─ ✅ 构建成功 → 检查 open issue → 关闭已修复的 issue
```

## CI 脚本注意事项

- **禁止**将多行文本直接写入 `$GITHUB_OUTPUT` — 会触发 `Invalid format` 错误
- 使用单行值或 heredoc 格式输出多行内容
- 构建日志 artifact 使用 `if: always()` 确保失败时也能上传
- ccache 已启用；命中率在 step summary 中查看

### gh 命令网络问题

GitHub CLI 偶尔会遇到网络连接问题：
```
Post "https://api.github.com/graphql": EOF
```

**原因**：GitHub API 服务器意外关闭连接、网络波动、API 限流等临时性问题。

**处理方式**：直接重试同一命令即可。

## 文档维护

**重要变更时及时更新本文档：**
- 代码源变更（如 GitCode 切换）
- Workflow 流程调整
- Slash 命令增删或功能变化
- 项目定位或工作边界调整

> 修改 CLAUDE.md 后需提交并推送到远程仓库。