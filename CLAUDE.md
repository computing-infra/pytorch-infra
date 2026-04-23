# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

本仓库用于**每日集成验证** [Ascend/pytorch](https://gitcode.com/Ascend/pytorch.git) 与 PyTorch nightly 版本的编译兼容性，以及**代码静态扫描**，同时提供 [pytorch/pytorch](https://github.com/pytorch/pytorch) 的**wheel 构建**功能。

### 核心定位
- **每日集成**：自动拉取 PyTorch nightly 和 Ascend/pytorch 最新代码进行编译验证
- **代码扫描**：定期对 Ascend/pytorch 进行代码静态分析
- **PyTorch 构建**：每日构建 pytorch/pytorch 的 CPU wheel（x86，多 Python 版本）
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

# 手动触发构建（x86）
gh workflow run nightly-build.yml --repo computing-infra/pytorch-infra

# 手动触发构建（ARM）
gh workflow run nightly-build-arm.yml --repo computing-infra/pytorch-infra

# 手动触发 NPU 构建+测试
gh workflow run npu-test.yml --repo computing-infra/pytorch-infra

# 手动触发 lint 检查
gh workflow run lint.yml --repo computing-infra/pytorch-infra

# 手动触发 PyTorch wheel 构建
gh workflow run pytorch-wheel.yml --repo computing-infra/pytorch-infra

# 手动触发 PyTorch wheel 构建（指定参数）
gh workflow run pytorch-wheel.yml --repo computing-infra/pytorch-infra \
  -f pytorch_ref=v2.5.0 -f python_version=cp311

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

### Workflow 架构总览

| Workflow | 平台 | 环境 | 触发方式 | 用途 |
|----------|------|------|----------|------|
| `nightly-build.yml` | x86_64 | `ubuntu-22.04` | 每日三次 + 手动 | Ascend/pytorch 编译验证（无 NPU） |
| `nightly-build-arm.yml` | aarch64 | 自托管 NPU runner | 每日三次 + 手动 | Ascend/pytorch ARM 编译验证 |
| `npu-test.yml` | aarch64 | 自托管 NPU + Docker | 手动/PR | Ascend/pytorch 构建 + NPU 真实测试 |
| `lint.yml` | x86_64 | `ubuntu-22.04` | 每周一 + 手动 | Ascend/pytorch 代码静态扫描 |
| `pytorch-wheel.yml` | x86_64 | PyTorch 官方镜像 | 每日一次 + 手动 | pytorch/pytorch wheel 构建 |

### nightly-build.yml（x86 编译验证）
- **触发方式**：每日三次（UTC 22:00/03:00/08:00，即北京时间 06:00/11:00/16:00），或手动触发
- **运行环境**：`ubuntu-22.04`，Python 3.11
- **特点**：使用内置桩库编译，无 CANN 依赖，仅需 GCC
- **构建流程**：
  1. 安装 PyTorch nightly（CPU 版）
  2. 克隆 Ascend/pytorch（含子模块）
  3. 执行 `python setup.py build bdist_wheel` 构建 wheel
  4. 上传构建产物（构建日志，成功时上传 wheel）

### nightly-build-arm.yml（ARM 编译验证）
- **触发方式**：每日三次（UTC 22:00/03:00/08:00），或手动触发
- **运行环境**：自托管 `npu-910b` runner + Docker 容器
- **Docker 镜像**：`swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder`
- **特点**：跳过 auditwheel repair（`AUDITWHEEL_PLAT=skip`），因 torch_npu 依赖外部 CANN

### npu-test.yml（NPU 构建 + 测试）
- **触发方式**：手动触发 或 PR 修改 workflow 文件时触发
- **运行环境**：自托管 NPU runner + Docker，挂载真实 NPU 设备（`/dev/davinci*`）
- **流程**：构建 → 安装 wheel → 验证 NPU 可用性 → 运行 `test_device.py`
- **关键**：使用 `ci/build.sh` 脚本构建，而非 `setup.py`

### Workflow: lint.yml（代码静态扫描）
- **触发方式**：每周一 UTC 10:00（北京时间 18:00），或手动触发
- **运行环境**：`ubuntu-22.04`，Python 3.11
- **检查流程**：克隆 → 应用 lint 配置 → lintrunner 扫描 → 生成报告
- **可选输入**：`ascend_commit` 参数指定要扫描的 commit

### pytorch-wheel.yml（PyTorch Wheel 构建）
- **触发方式**：每日一次（UTC 22:00，北京时间次日 06:00），或手动触发
- **运行环境**：`ubuntu-22.04` + PyTorch 官方镜像 `ghcr.io/pytorch/test-infra:cpu-x86_64-latest`
- **特点**：使用 manylinux 镜像内置 Python，构建 CPU only wheel
- **构建矩阵**：4 个 Python 版本（cp310, cp311, cp312, cp313）并行构建
- **构建流程**：
  1. Checkout pytorch/pytorch（含子模块）
  2. 配置 sccache 编译缓存
  3. 执行 `python setup.py build bdist_wheel`
  4. auditwheel repair wheel
  5. 上传 wheel 和构建日志
- **手动触发参数**：
  - `pytorch_ref`: 指定分支/tag/commit（默认 `main`）
  - `python_version`: 指定 Python 版本（默认 `cp311`）

### Issue 追踪 (`issues/`)
- 格式：`YYYY-MM-DD-NNN-<模块描述>.md`
- 记录根本原因、受影响文件、修复建议

### Linter 配置 (`lint-config/`)
- `.lintrunner.toml`：lintrunner 配置，定义检查规则
- `.clang-format`：C++ 代码格式化配置

### Linter 工具 (`lint-tools/adapters/`)
从 PyTorch 复制的 linter 适配器脚本：
- `flake8_linter.py`：Python PEP8 检查
- `clangformat_linter.py`：C++ 代码格式化检查
- `newlines_linter.py`：换行符检查
- `grep_linter.py`：通用模式匹配检查

## 构建环境差异

| 平台 | 构建方式 | ccache | auditwheel |
|------|----------|--------|------------|
| x86 | `setup.py build bdist_wheel` | 5G | 正常执行 |
| ARM | `setup.py build bdist_wheel` | 10G | `skip` |
| NPU Test | `ci/build.sh --python=3.11` | 10G（容器内） | `skip` |

**关键环境变量**：
- `MAX_JOBS=$(nproc)`：并行编译数
- `DISABLE_INSTALL_TORCHAIR=FALSE`：启用 torchair 构建
- `BUILD_WITHOUT_SHA=1`：跳过 SHA 验证
- `AUDITWHEEL_PLAT=skip`：跳过 wheel 修复（ARM/NPU）

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