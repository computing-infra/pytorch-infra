# Linter 规则迁移计划

本文档记录从 PyTorch 仓库迁移静态扫描规则到 pytorch-infra 的计划。

## 当前状态

### 已迁移规则 (17个)

| Linter | 功能 | 状态 |
|--------|------|------|
| CLANGFORMAT | C++ 代码格式化检查 | ✅ 已完成 |
| NEWLINE | 换行符检查（确保 LF） | ✅ 已完成 |
| SPACES | 尾部空格检查 | ✅ 已完成 |
| TABS | Tab 检查（应使用空格） | ✅ 已完成 |
| NOBREAKSPACE | 非中断空格检查 | ✅ 已完成 |
| RUFF | Python 综合检查 + 格式化（替代 FLAKE8） | ✅ 第一批 |
| CODESPELL | 拼写错误检查 | ✅ 第一批 |
| SHELLCHECK | Shell 脚本检查 | ✅ 第一批 |
| ACTIONLINT | GitHub Actions 检查 | ✅ 第一批 |
| ROOT_LOGGING | 禁止直接使用 root logger | ✅ 第二批 |
| NOQA | 检查未限定的 noqa | ✅ 第二批 |
| TYPEIGNORE | 检查未限定的 type: ignore | ✅ 第二批 |
| PYFMT | Python 格式化 (usort + ruff) | ✅ 第二批 |
| C10_UNUSED | 检查已弃用的 C10_UNUSED 宏 | ✅ 第三批 |
| C10_NODISCARD | 检查已弃用的 C10_NODISCARD 宏 | ✅ 第三批 |
| RAWTHROW | 禁止直接 throw 语句 | ✅ 第三批 |
| INCLUDE | 检查 #include 格式 | ✅ 第三批 |

**说明**：
- FLAKE8 已被 RUFF 替代（RUFF 包含 E+F 规则，覆盖 FLAKE8 功能）
- ROOT_LOGGING 不检查测试文件（测试场景允许直接使用 root logger）
- RAWTHROW 排除了 Python binding 和特定异常处理模块
- INCLUDE 统一使用尖括号格式 `#include <torch_npu/...>`

---

## 迁移计划

### 第一批：通用代码质量工具 (优先级：高)

**预计完成时间**：1-2 天

| Linter | 功能 | 迁移难度 | 价值 | 文件 |
|--------|------|----------|------|------|
| **RUFF** | Python 综合检查 + 格式化 | 低 | ⭐⭐⭐⭐⭐ | `ruff_linter.py` |
| **CODESPELL** | 拼写错误检查 | 低 | ⭐⭐⭐⭐ | `codespell_linter.py` |
| **SHELLCHECK** | Shell 脚本检查 | 低 | ⭐⭐⭐⭐ | `shellcheck_linter.py` |
| **ACTIONLINT** | GitHub Actions 检查 | 低 | ⭐⭐⭐⭐ | `actionlint_linter.py` |

**迁移步骤**：

1. 复制 linter 适配器脚本到 `lint-tools/adapters/`
2. 更新 `lint-config/.lintrunner.toml` 添加规则
3. 添加必要的配置文件（如 `ruff.toml`）
4. 测试验证

**预期效果**：
- RUFF：替代 FLAKE8，提供更快的检查和自动修复
- CODESPELL：发现代码中的拼写错误
- SHELLCHECK：检查 `.ci/` 目录下的 shell 脚本
- ACTIONLINT：检查 GitHub Actions workflow 语法

---

### 第二批：Python 最佳实践 (优先级：中)

**预计完成时间**：1 天

| Linter | 功能 | 迁移难度 | 价值 |
|--------|------|----------|------|
| **ROOT_LOGGING** | 禁止直接使用 root logger | 低 | ⭐⭐⭐⭐ |
| **NOQA** | 检查未限定的 `# noqa` | 低 | ⭐⭐⭐ |
| **TYPEIGNORE** | 检查未限定的 `# type: ignore` | 低 | ⭐⭐⭐ |
| **PYFMT** | Python 格式化 (usort + ruff) | 中 | ⭐⭐⭐⭐ |

**迁移步骤**：

1. 使用 `grep_linter.py` 实现 ROOT_LOGGING、NOQA、TYPEIGNORE
2. 复制 `pyfmt_linter.py` 实现 PYFMT
3. 更新 `.lintrunner.toml`
4. 测试验证

**预期效果**：
- ROOT_LOGGING：强制使用 `log = logging.getLogger(__name__)`
- NOQA：要求 `# noqa: E501` 而非 `# noqa`
- TYPEIGNORE：要求 `# type: ignore[xxxx]` 而非 `# type: ignore`
- PYFMT：自动格式化 Python 代码

---

### 第三批：C++ 最佳实践 (优先级：中)

**预计完成时间**：1-2 天

| Linter | 功能 | 迁移难度 | 价值 | 状态 |
|--------|------|----------|------|------|
| **CLANGTIDY** | C++ 静态分析 | 高 | ⭐⭐⭐⭐⭐ | ⏳ 暂缓 |
| **RAWTHROW** | 禁止直接 `throw` | 低 | ⭐⭐⭐⭐ | ✅ 已完成 |
| **INCLUDE** | `#include` 格式检查 | 低 | ⭐⭐⭐ | ✅ 已完成 |
| **C10_UNUSED** | 检查已弃用宏 | 低 | ⭐⭐⭐ | ✅ 已完成 |
| **C10_NODISCARD** | 检查已弃用宏 | 低 | ⭐⭐⭐ | ✅ 已完成 |

**迁移步骤**：

1. CLANGTIDY 需要配置编译数据库，较为复杂
2. 其他规则使用 `grep_linter.py` 实现
3. 更新 `.lintrunner.toml`
4. 测试验证

**注意事项**：
- CLANGTIDY 需要 `compile_commands.json`，可能需要调整构建流程
- RAWTHROW 需要定义 Ascend/pytorch 允许的异常处理宏

**预期效果**：
- CLANGTIDY：发现 C++ 代码潜在问题
- RAWTHROW：统一异常处理方式
- INCLUDE：统一 `#include <>` 格式
- C10_UNUSED/C10_NODISCARD：检查已弃用的宏

---

### 第四批：构建系统检查 (优先级：低)

**预计完成时间**：1 天

| Linter | 功能 | 迁移难度 | 价值 |
|--------|------|----------|------|
| **CMAKE** | CMake 文件检查 | 中 | ⭐⭐⭐⭐ |
| **CMAKE_MINIMUM_REQUIRED** | CMake/pyproject 最低版本 | 中 | ⭐⭐⭐ |
| **PYPROJECT** | pyproject.toml 检查 | 低 | ⭐⭐⭐ |

**迁移步骤**：

1. 复制 cmake 相关 linter 脚本
2. 添加 `.cmakelintrc` 配置文件
3. 更新 `.lintrunner.toml`
4. 测试验证

---

### 第五批：测试相关 (优先级：低)

**预计完成时间**：1 天

| Linter | 功能 | 迁移难度 | 价值 |
|--------|------|----------|------|
| **TEST_HAS_MAIN** | 测试文件入口检查 | 低 | ⭐⭐⭐ |
| **COPYRIGHT** | 检查机密代码 | 低 | ⭐⭐ |

**迁移步骤**：

1. 复制 `test_has_main_linter.py`
2. 使用 `grep_linter.py` 实现 COPYRIGHT
3. 更新 `.lintrunner.toml`
4. 测试验证

---

## 暂不迁移的规则

### PyTorch 特有架构

| Linter | 原因 |
|--------|------|
| CLANGTIDY_EXECUTORCH_COMPATIBILITY | ExecuTorch 专用 |
| STABLE_SHIM_VERSION/USAGE | PyTorch stable shim 专用 |
| HEADER_ONLY_LINTER | PyTorch header-only API 专用 |
| GB_REGISTRY | PyTorch dynamo 专用 |
| META_NO_CREATE_UNBACKED | PyTorch meta registration 专用 |
| ATEN_CPU_GPU_AGNOSTIC | ATen CPU 专用 |

### CUDA 相关

| Linter | 原因 |
|--------|------|
| CUBINCLUDE | CUDA cub 库专用 |
| RAWCUDA | CUDA API 专用 |
| RAWCUDADEVICE | CUDA API 专用 |

### 需要评估

| Linter | 说明 |
|--------|------|
| NATIVEFUNCTIONS | 需确认 Ascend/pytorch 是否有类似 yaml |
| PYBIND11_INCLUDE | 需确认 torch_npu 的 pybind 使用情况 |
| PYBIND11_SPECIALIZATION | 同上 |
| TESTOWNERS | 需要 owner 机制支持 |

---

## 迁移进度追踪

| 批次 | 状态 | 开始时间 | 完成时间 |
|------|------|----------|----------|
| 已完成 (6个基础规则) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第一批 (通用工具) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第二批 (Python实践) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第三批 (C++实践) | ✅ 完成 (除CLANGTIDY) | 2026-03-31 | 2026-03-31 |
| 第四批 (构建系统) | ⏳ 待开始 | - | - |
| 第五批 (测试相关) | ⏳ 待开始 | - | - |

**验证记录**：
- 2026-03-31: 第三批迁移后验证成功，workflow运行正常
  - 检测到 Ascend/pytorch 存在 962 条 lint 问题
  - 问题分布：CLANGFORMAT(349), INCLUDE(283), SPACES(251), RAWTHROW(165), NEWLINE(93), TABS(12), C10_UNUSED(3), NOQA(3), C10_NODISCARD(1), CODESPELL(1), PYFMT(1), RUFF(1), SHELLCHECK(1)
  - lint 报告通过 artifact 上传，不自动创建 issue

---

## 配置文件清单

迁移完成后需要维护的配置文件：

| 文件 | 用途 | 状态 |
|------|------|------|
| `lint-config/.lintrunner.toml` | Linter 主配置 | ✅ 已创建 |
| `lint-config/.clang-format` | C++ 格式化配置 | ✅ 已创建 |
| `lint-config/ruff.toml` | Ruff 配置 | ✅ 已创建 |
| `lint-config/dictionary.txt` | Codespell 拼写字典 | ✅ 已创建 |
| `lint-config/.cmakelintrc` | CMake lint 配置 | ⏳ 待创建 |
| `lint-config/codespell.toml` | Codespell 配置 | ⏳ 待创建 | |

---

## 参考资料

- PyTorch linter 配置：https://github.com/pytorch/pytorch/blob/main/.lintrunner.toml
- Lintrunner 文档：https://github.com/suo/lintrunner
- Ruff 文档：https://docs.astral.sh/ruff/
- Clang-Tidy 文档：https://clang.llvm.org/extra/clang-tidy/