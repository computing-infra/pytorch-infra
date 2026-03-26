# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

本仓库用于**每日集成验证** [Ascend/pytorch](https://github.com/Ascend/pytorch) 与 PyTorch nightly 版本的编译兼容性。

### 核心定位
- **每日集成**：自动拉取 PyTorch nightly 和 Ascend/pytorch 最新代码进行编译验证
- **问题追踪**：CI 失败时，使用 `/analyze-failure` 分析错误、`/report-issue` 生成 issue 文档
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
gh run list --repo kerer-ai/pytorch-npu --limit 5

# 手动触发构建
gh workflow run nightly-build.yml --repo kerer-ai/pytorch-npu

# 查看失败运行的日志
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed
```

### 本地 Ascend/pytorch 克隆
```bash
# 源码分析用的克隆路径
/root/ascend_pytorch_tmp

# 若不存在则克隆
git clone --depth=1 https://github.com/Ascend/pytorch.git /root/ascend_pytorch_tmp
```

### PyTorch Nightly 头文件
```bash
# API 对比时使用的头文件路径
/usr/local/lib/python3.12/dist-packages/torch/include/
```

## 架构

### Workflow: `.github/workflows/nightly-build.yml`
- **触发方式**：每日 UTC 02:00 自动触发，或通过 `workflow_dispatch` 手动触发
- **运行环境**：`ubuntu-22.04`，Python 3.11
- **构建流程**：
  1. 安装 PyTorch nightly（CPU 版）
  2. 克隆 Ascend/pytorch（含子模块）
  3. 执行 `python setup.py build bdist_wheel` 构建 wheel
  4. 上传构建产物（构建日志，成功时上传 wheel）

### Issue 追踪 (`issues/`)
- 格式：`YYYY-MM-DD-NNN-<模块描述>.md`
- 记录根本原因、受影响文件、修复建议

## Slash 命令

| 命令 | 用途 |
|------|------|
| `/analyze-failure` | 分析最新失败的 CI 运行，定位根本原因 |
| `/report-issue` | 根据分析结果创建 issue 文档 |

### 典型工作流
```
CI 失败 → /analyze-failure → /report-issue → 输出修复建议
```

## CI 脚本注意事项

- **禁止**将多行文本直接写入 `$GITHUB_OUTPUT` — 会触发 `Invalid format` 错误
- 使用单行值或 heredoc 格式输出多行内容
- 构建日志 artifact 使用 `if: always()` 确保失败时也能上传
- ccache 已启用；命中率在 step summary 中查看