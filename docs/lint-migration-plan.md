# Linter 规则迁移计划

本文档记录从 PyTorch 仓库迁移静态扫描规则到 pytorch-infra 的计划。

## 当前状态

### 已迁移规则 (21个)

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
| CMAKE | CMake 文件检查 | ✅ 第四批 |
| PYPROJECT | pyproject.toml 检查 | ✅ 第四批 |
| CMAKE_MINIMUM_REQUIRED | CMake/pyproject 最低版本 | ✅ 第四批 |
| COPYRIGHT | 检查机密代码 | ✅ 第五批 |

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

#### 规则详细分析

| Linter | 功能 | 迁移难度 | 价值 | 改造需求 |
|--------|------|----------|------|----------|
| **CMAKE** | CMake 文件检查 | 中 | ⭐⭐⭐⭐ | 低 - 仅调整 patterns |
| **CMAKE_MINIMUM_REQUIRED** | CMake/pyproject 最低版本 | 中 | ⭐⭐⭐ | 高 - 移除 PyTorch 内部依赖 |
| **PYPROJECT** | pyproject.toml 检查 | 低 | ⭐⭐⭐ | 无 - 直接复制 |

#### 1. CMAKE 规则分析

**PyTorch 配置**：
```toml
[[linter]]
code = 'CMAKE'
include_patterns = ["**/*.cmake", "**/*.cmake.in", "**/CMakeLists.txt"]
exclude_patterns = [
    'cmake/Modules/**',
    'cmake/Modules_CUDA_fix/**',
    'cmake/Caffe2Config.cmake.in',
    'aten/src/ATen/ATenCONFIG.cmake.in',
    'cmake/TorchConfig.cmake.in',
    'cmake/TorchConfigVersion.cmake.in',
    'cmake/cmake_uninstall.cmake.i',
    'fb/**',
    '**/fb/**',
]
command = ['uv', 'run', '--script', 'tools/linter/adapters/cmake_linter.py', '--config=.cmakelintrc', '--', '@{{PATHSFILE}}']
```

**Ascend/pytorch 结构**：
- 主 CMakeLists.txt 在根目录，使用 cmake_minimum_required(VERSION 3.18)
- 子目录 CMakeLists.txt：`torch_npu/csrc/**/*.cmake`, `examples/**/*.cmake`, `test/cpp/**/*.cmake`
- 第三方依赖：`third_party/**/*.cmake`（需排除）

**改造方案**：
- 复制 `cmake_linter.py` 脚本
- 创建 `.cmakelintrc` 配置文件（沿用 PyTorch 配置）
- 调整 exclude_patterns：排除 `third_party/**`, `torch_npu/csrc/aten/**`

#### 2. PYPROJECT 规则分析

**PyTorch 配置**：
```toml
[[linter]]
code = 'PYPROJECT'
include_patterns = ["**/pyproject.toml"]
command = ['uv', 'run', '--script', 'tools/linter/adapters/pyproject_linter.py', '--', '@{{PATHSFILE}}']
```

**功能**：
- 检查 `project.requires-python` 是否为有效 Python 版本范围
- 检查 `project.classifiers` 是否为字符串数组且无重复

**Ascend/pytorch 结构**：
- 无 pyproject.toml 文件（使用 setup.py）

**改造方案**：
- 直接复制脚本，无需改造
- 实际运行时不会检查任何文件（无匹配）

#### 3. CMAKE_MINIMUM_REQUIRED 规则分析

**PyTorch 配置**：
```toml
[[linter]]
code = 'CMAKE_MINIMUM_REQUIRED'
include_patterns = ["**/pyproject.toml", "**/CMakeLists.txt", "**/CMakeLists.txt.in", "**/*.cmake", "**/*.cmake.in", "**/*requirements*.txt", "**/*requirements*.in"]
command = ['uv', 'run', '--script', 'tools/linter/adapters/cmake_minimum_required_linter.py', '--', '@{{PATHSFILE}}']
```

**关键依赖问题**：
```python
# 原脚本依赖 PyTorch 内部模块
from tools.setup_helpers.env import CMAKE_MINIMUM_VERSION_STRING
CMAKE_MINIMUM_VERSION_STRING = "3.27"  # PyTorch 要求版本
```

**Ascend/pytorch CMake 版本**：
- 根目录 CMakeLists.txt：`cmake_minimum_required(VERSION 3.18)`
- 其他 CMakeLists.txt：无显式版本要求

**改造方案**：
- 复制脚本并移除对 `tools.setup_helpers.env` 的依赖
- 硬编码 `CMAKE_MINIMUM_VERSION = "3.18"`（Ascend/pytorch 要求版本）
- 调整检查逻辑：只检查根目录 CMakeLists.txt 的版本一致性
- 排除 `third_party/**` 目录

#### 迁移步骤

1. 复制 linter 适配器脚本到 `lint-tools/adapters/`
   - `cmake_linter.py`（直接复制）
   - `pyproject_linter.py`（直接复制）
   - `cmake_minimum_required_linter.py`（改造后复制）

2. 创建配置文件
   - `lint-config/.cmakelintrc`（沿用 PyTorch 配置）

3. 更新 `lint-config/.lintrunner.toml` 添加规则
   - 调整 include/exclude patterns 适配 Ascend/pytorch

4. 测试验证

---

### 第五批：测试相关 (优先级：低)

**预计完成时间**：1 天

#### 规则详细分析

| Linter | 功能 | 迁移难度 | 价值 | 改造需求 |
|--------|------|----------|------|----------|
| **TEST_HAS_MAIN** | 测试文件入口检查 | 低 | ⭐⭐⭐ | 低 - 调整 patterns |
| **COPYRIGHT** | 检查机密代码 | 低 | ⭐⭐ | 无 - 直接复制 |

#### 1. TEST_HAS_MAIN 规则分析

**PyTorch 配置**：
```toml
[[linter]]
code = 'TEST_HAS_MAIN'
include_patterns = ['test/**/test_*.py']
exclude_patterns = [
    'test/run_test.py',
    '**/fb/**',
    # ... 大量排除项
]
command = ['uv', 'run', '--script', 'tools/linter/adapters/test_has_main_linter.py', '--', '@{{PATHSFILE}}']
```

**功能**：
- 检查测试文件是否有 `if __name__ == "__main__"` 块
- 确保测试文件调用 `run_tests()` 或抛出异常
- 保证测试能在 OSS CI 中运行

**Ascend/pytorch 结构**：
- 有 614 个 `test_*.py` 文件
- 只有 47 个文件有 `if __name__` 块
- 需要排除大量不适用该规则的测试文件

**改造方案**：
- 复制 `test_has_main_linter.py` 脚本
- 调整 exclude_patterns 适配 Ascend/pytorch 测试结构
- 由于 Ascend/pytorch 测试框架可能不同，可考虑仅保留 COPYRIGHT 规则

#### 2. COPYRIGHT 规则分析

**PyTorch 配置**：
```toml
[[linter]]
code = 'COPYRIGHT'
include_patterns = ['**']
exclude_patterns = ['.lintrunner.toml', 'fb/**', '**/fb/**']
command = [
    'python3',
    'tools/linter/adapters/grep_linter.py',
    '--pattern=Confidential and proprietary',
    '--linter-name=COPYRIGHT',
    '--error-name=Confidential Code',
    '--error-description=Proprietary and confidential source code should not be contributed to PyTorch codebase',
    '--',
    '@{{PATHSFILE}}'
]
```

**功能**：
- 检测代码中是否包含 "Confidential and proprietary" 字样
- 防止机密代码被提交到开源仓库

**Ascend/pytorch 结构**：
- 当前未检测到机密代码
- 作为预防措施保留此规则

**改造方案**：
- 使用 `grep_linter.py` 实现，无需创建新脚本
- 直接在 `.lintrunner.toml` 中添加配置

#### 迁移决策

由于 Ascend/pytorch 测试框架与 PyTorch 可能存在差异，且大量测试文件不符合 `TEST_HAS_MAIN` 规则要求，决定：
1. **COPYRIGHT**：迁移，用于防止机密代码提交
2. **TEST_HAS_MAIN**：暂缓迁移，待确认 Ascend/pytorch 测试框架要求

#### 迁移步骤

1. 在 `.lintrunner.toml` 中添加 COPYRIGHT 规则配置
2. 测试验证

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
| TEST_HAS_MAIN | Ascend/pytorch 测试框架差异，614个测试文件仅47个有main块 |
| CLANGTIDY | 需要 compile_commands.json，迁移难度高 |

---

## 迁移进度追踪

| 批次 | 状态 | 开始时间 | 完成时间 |
|------|------|----------|----------|
| 已完成 (6个基础规则) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第一批 (通用工具) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第二批 (Python实践) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第三批 (C++实践) | ✅ 完成 (除CLANGTIDY) | 2026-03-31 | 2026-03-31 |
| 第四批 (构建系统) | ✅ 完成 | 2026-03-31 | 2026-03-31 |
| 第五批 (测试相关) | ✅ 完成 (COPYRIGHT, TEST_HAS_MAIN暂缓) | 2026-03-31 | 2026-03-31 |

**验证记录**：
- 2026-03-31: 第三批迁移后验证成功，workflow运行正常
  - 检测到 Ascend/pytorch 存在 962 条 lint 问题
  - 问题分布：CLANGFORMAT(349), INCLUDE(283), SPACES(251), RAWTHROW(165), NEWLINE(93), TABS(12), C10_UNUSED(3), NOQA(3), C10_NODISCARD(1), CODESPELL(1), PYFMT(1), RUFF(1), SHELLCHECK(1)
  - lint 报告通过 artifact 上传，不自动创建 issue
- 2026-03-31: 第四批迁移后验证成功
  - 新增检测：CMAKE(42), CODESPELL(205), RUFF(225错误+8876警告), SHELLCHECK(32), PYFMT(951)
  - 需要在 workflow 中安装 uv 工具用于运行内联依赖脚本
  - CMAKE 检测到 `if()` 语句中的额外空格问题
- 2026-03-31: 第五批迁移后验证成功
  - COPYRIGHT 规则正常工作，未检测到机密代码
  - TEST_HAS_MAIN 暂缓迁移

---

## 配置文件清单

迁移完成后需要维护的配置文件：

| 文件 | 用途 | 状态 |
|------|------|------|
| `lint-config/.lintrunner.toml` | Linter 主配置 | ✅ 已创建 |
| `lint-config/.clang-format` | C++ 格式化配置 | ✅ 已创建 |
| `lint-config/ruff.toml` | Ruff 配置 | ✅ 已创建 |
| `lint-config/dictionary.txt` | Codespell 拼写字典 | ✅ 已创建 |
| `lint-config/.cmakelintrc` | CMake lint 配置 | ✅ 已创建 |
| `lint-config/codespell.toml` | Codespell 配置 | ⏳ 待创建 | |

---

## 参考资料

- PyTorch linter 配置：https://github.com/pytorch/pytorch/blob/main/.lintrunner.toml
- Lintrunner 文档：https://github.com/suo/lintrunner
- Ruff 文档：https://docs.astral.sh/ruff/
- Clang-Tidy 文档：https://clang.llvm.org/extra/clang-tidy/

---

## 迁移套路总结

### 标准迁移流程

```
1. 分析 PyTorch 原规则
   ├── 查看 .lintrunner.toml 中的规则配置
   ├── 查看 linter 适配器脚本实现
   └── 查看相关配置文件（如 .cmakelintrc）

2. 分析 Ascend/pytorch 结构
   ├── 检查目标文件是否存在（include_patterns）
   ├── 检查需要排除的目录（third_party, generated 等）
   └── 检查是否有 PyTorch 内部依赖

3. 确定改造需求
   ├── 低改造：仅需调整 include/exclude patterns
   ├── 中改造：需要调整检查逻辑或参数
   ├── 高改造：需要移除 PyTorch 内部依赖或重写部分逻辑
   └── 不迁移：PyTorch 特有功能，Ascend/pytorch 不适用

4. 执行迁移
   ├── 复制 linter 适配器脚本到 lint-tools/adapters/
   ├── 创建/修改配置文件
   ├── 更新 lint-config/.lintrunner.toml
   └── 本地测试验证

5. CI 验证
   ├── 触发 workflow 运行
   ├── 检查 lint 报告
   ├── 记录验证结果
   └── 更新文档
```

### 关键改造模式

| 改造类型 | 说明 | 示例 |
|---------|------|------|
| **Patterns 调整** | 适配目标仓库目录结构 | `include_patterns = ['torch_npu/**/*.py']` |
| **依赖移除** | 移除 PyTorch 内部模块依赖 | `CMAKE_MINIMUM_REQUIRED` 移除 `tools.setup_helpers.env` |
| **参数调整** | 调整检查参数或阈值 | CMake 版本从 3.27 改为 3.18 |
| **规则合并** | 合并相似规则减少冗余 | RUFF 替代 FLAKE8 |
| **规则排除** | 不迁移 PyTorch 特有规则 | CUDA 相关规则不迁移 |

### 文件命名规范

| 类型 | 路径 | 说明 |
|------|------|------|
| Linter 脚本 | `lint-tools/adapters/<name>_linter.py` | 统一使用 `_linter.py` 后缀 |
| 配置文件 | `lint-config/<config_file>` | 所有配置文件集中管理 |
| 主配置 | `lint-config/.lintrunner.toml` | lintrunner 主配置文件 |

### 验证检查清单

- [ ] include_patterns 是否匹配目标文件
- [ ] exclude_patterns 是否排除第三方/生成代码
- [ ] 脚本依赖是否已移除/替换
- [ ] 配置文件是否已创建
- [ ] workflow 是否正常运行
- [ ] lint 报告是否生成