# PyTorch Workflow 测试用例迁移分析

## 概述

本文分析 PyTorch 官方仓库的 workflow 测试流程，识别适合迁移到 NPU（华为昇腾）的测试用例，并给出具体迁移方案。

**分析日期**: 2026-03-31

**相关仓库**:
- PyTorch 官方: `/home/wangsike/workspace/pytorch/pytorch/pytorch`
- Ascend/pytorch (NPU 插件): `/home/wangsike/workspace/pytorch/ascend_pytorch/pytorch`

---

## 一、仓库架构分析

### 1.1 PyTorch 官方仓库测试架构

#### 目录结构

```
pytorch/test/
├── test_torch.py          # 基础张量操作测试
├── test_nn.py             # nn 模块测试
├── test_autograd.py       # 自动微分测试
├── test_ops.py            # 操作测试
├── test_indexing.py       # 索引操作测试
├── test_reductions.py     # 归约操作测试
├── test_view_ops.py       # 视图操作测试
├── test_jit.py            # JIT 编译器测试
├── distributed/           # 分布式训练测试
│   ├── test_c10d.py
│   ├── tensor/           # DTensor 测试
│   ├── fsdp/             # FSDP 测试
│   ├── pipeline/         # Pipeline 并行测试
│   └── _composable/      # 可组合分布式测试
├── inductor/              # Inductor 编译器测试
├── dynamo/                # Dynamo 测试
├── onnx/                  # ONNX 导出测试
├── fx/                    # FX 中间表示测试
├── jit/                   # JIT 子模块测试
├── profiler/              # Profiler 测试
├── cpp/                   # C++ API 测试
├── cpp_extensions/        # C++ 扩展测试
├── nn/                    # nn 子模块测试
│   └── attention/        # Attention 模块测试
├── mobile/                # 移动端测试
├── package/               # 打包测试
├── export/                # 导出测试
└── functorch/             # functorch 测试
```

#### 测试发现机制 (`tools/testing/discover_tests.py`)

```python
TESTS = discover_tests(
    cpp_tests_dir=CPP_TESTS_DIR,
    blocklisted_patterns=[
        "ao",
        "custom_backend",
        "custom_operator",
        "fx",      # 由 test_fx.py 执行
        "jit",     # 由 test_jit.py 执行
        "mobile",
        "onnx_caffe2",
        "package", # 由 test_package.py 执行
        "quantization", # 由 test_quantization.py 执行
        "autograd", # 由 test_autograd.py 执行
    ],
    blocklisted_tests=[...],
    extra_tests=[...]
)
```

### 1.2 Ascend/pytorch 架构

#### 与 PyTorch 的集成方式

Ascend/pytorch 作为 PyTorch 的第三方硬件插件工作，核心机制：

1. **设备标识**: 使用 `PRIVATEUSE1` 作为 NPU 设备类型
2. **包名**: `torch_npu`
3. **注册机制**: 通过 PyTorch 的 extension device 机制注册

```python
# 典型导入方式
import torch
import torch_npu

# 设备使用
device = torch.device("npu")  # 或 "privateuseone"
tensor = torch.randn(3, 3).to("npu")
```

#### 现有测试结构

```
ascend_pytorch/test/
├── test_npu.py              # NPU 核心功能测试
├── test_autocast.py         # 自动混合精度测试
├── test_torch.py            # 从 PyTorch 同步并适配
├── test_nn.py               # 从 PyTorch 同步并适配
├── test_autograd.py         # 从 PyTorch 同步并适配
├── test_ops.py              # 从 PyTorch 同步并适配
├── npu/                     # NPU 特有测试
│   ├── test_amp.py         # AMP 功能
│   ├── test_aclgraph_*.py  # ACL Graph 功能
│   ├── test_storage.py     # 存储管理
│   ├── test_torch_npu.py   # torch_npu 特定功能
│   └── test_public_bindings.py # 公开接口校验
├── distributed/             # 分布式测试（HCCL）
├── unsupported_test_cases/  # 不支持的测试配置
│   ├── .pytorch-disabled-tests.json # 跳过的测试用例
│   ├── disabled_tests_type.json     # 跳过原因分类
│   └── error_type.json              # 错误类型分类
├── testfiles_synchronized.txt  # 从 PyTorch 同步的文件列表
├── adapt_testcases_to_npu.py    # CUDA→NPU 适配脚本
└── run_test.py                   # 测试运行脚本
```

---

## 二、PyTorch Workflow 测试流程分析

### 2.1 核心 Workflow 文件

| Workflow | 用途 | 备注 |
|----------|------|------|
| `_linux-test.yml` | Linux CUDA/ROCm 测试 | 主要测试流程 |
| `_xpu-test.yml` | Intel XPU 测试 | **第三方硬件参考** |
| `_rocm-test.yml` | AMD ROCm 测试 | GPU 硬件测试参考 |
| `_mac-test.yml` | macOS 测试 | CPU 测试 |
| `_win-test.yml` | Windows 测试 | CPU 测试 |
| `_linux-build.yml` | Linux 构建 | 构建 wheel |
| `_bazel-build-test.yml` | Bazel 构建测试 | Bazel 构建系统 |

### 2.2 XPU 测试 Workflow 分析（NPU 迁移参考）

`_xpu-test.yml` 是 Intel XPU 的测试流程，可作为 NPU 迁移的重要参考：

```yaml
# 关键配置
env:
  PYTORCH_TESTING_DEVICE_ONLY_FOR: "xpu"
  PYTHON_TEST_EXTRA_OPTION: "--xpu"
  NO_TEST_TIMEOUT: True
```

#### XPU 测试设置流程 (`setup-xpu/action.yml`)

```yaml
# 1. 环境检测
- timeout 30 xpu-smi discovery

# 2. GPU Flag 设置
GPU_FLAG=--device=/dev/mem --device=/dev/dri --group-add video

# 3. oneAPI 环境加载
source /opt/intel/oneapi/compiler/latest/env/vars.sh
source /opt/intel/oneapi/ccl/latest/env/vars.sh
source /opt/intel/oneapi/mpi/latest/env/vars.sh
```

### 2.3 测试脚本 (`test.sh`) 设备适配

```bash
# 设备特定设置
if [[ "$BUILD_ENVIRONMENT" == *cuda* || "$BUILD_ENVIRONMENT" == *rocm* ]]; then
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="cuda"
elif [[ "$BUILD_ENVIRONMENT" == *xpu* ]]; then
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="xpu"
  export PYTHON_TEST_EXTRA_OPTION="--xpu"
  export NO_TEST_TIMEOUT=True
elif [[ "$BUILD_ENVIRONMENT" == *pallas-tpu* ]]; then
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="tpu"
fi

# XPU Smoke 测试
test_python_smoke_xpu() {
  time python test/run_test.py --include test_transformers $PYTHON_TEST_EXTRA_OPTION
}
```

---

## 三、测试用例适配机制

### 3.1 CUDA → NPU 适配脚本

`adapt_testcases_to_npu.py` 的替换规则：

```python
replace_map = {
    ".cuda": ".npu",
    "onlyCUDA": "onlyPRIVATEUSE1",
    "dtypesIfCUDA": "dtypesIfPRIVATEUSE1",
    "(?<!common_)cuda(?=[\": ',])": "npu",
    "(?<!_)CUDA(?=[\": '])": "NPU",
    "TEST_CUDA": "TEST_PRIVATEUSE1"
}
```

### 3.2 已同步的测试文件

`testfiles_synchronized.txt` 列出的同步文件：

**JIT 测试**:
- `test/test_jit_disabled.py`
- `test/test_jit_fuser_legacy.py`
- `test/jit/test_*.py` (75+ 文件)

**ONNX 测试**:
- `test/onnx/test_*.py` (20+ 文件)

**Functorch 测试**:
- `test/functorch/*.py`

**Profiler 测试**:
- `test/profiler/test_*.py`

**其他测试**:
- `test/test_type_info.py`
- `test/test_dynamic_shapes.py`
- `test/test_fx_reinplace_pass.py`

### 3.3 不支持的测试分类

`disabled_tests_type.json` 的跳过原因：

| 类型 | 原因 | 示例 |
|------|------|------|
| `DTYPE` | 数据类型不支持 | complex128, complex64, bfloat16 某些操作 |
| `ERROR_MSG_UNMATCH` | 错误消息不匹配 | assertRaisesRegex 错误 |
| `NOT_SUPPORT` | 功能不支持 | Conv3DTranspose 某些配置 |
| `OTHER` | 其他原因 | ARM 架构不支持 |

---

## 四、建议迁移的测试用例

### 4.1 高优先级迁移（核心功能）

这些测试覆盖 NPU 的核心功能，必须迁移：

| 测试文件 | 用途 | 迁移难度 | 说明 |
|----------|------|----------|------|
| `test_torch.py` | 基础张量操作 | 中 | 已同步，需持续更新 |
| `test_nn.py` | nn 模块测试 | 中 | 已同步，需持续更新 |
| `test_autograd.py` | 自动微分 | 中 | 已同步，需持续更新 |
| `test_ops.py` | 操作测试 | 高 | 已同步，核心算子测试 |
| `test_npu.py` | NPU 特有功能 | 低 | 已存在，需扩展 |
| `test_autocast.py` | 自动混合精度 | 低 | 已存在 |

### 4.2 中优先级迁移（功能扩展）

这些测试覆盖重要功能，建议迁移：

| 测试文件/目录 | 用途 | 迁移难度 | 说明 |
|---------------|------|----------|------|
| `test_indexing.py` | 索引操作 | 中 | 基础功能 |
| `test_reductions.py` | 归约操作 | 中 | 基础功能 |
| `test_view_ops.py` | 视图操作 | 中 | 基础功能 |
| `test_tensor_creation_ops.py` | 张量创建 | 中 | 基础功能 |
| `test_shape_ops.py` | 形状操作 | 中 | 基础功能 |
| `test_unary_ufuncs.py` | 一元函数 | 中 | 数学运算 |
| `test_binary_ufuncs.py` | 二元函数 | 中 | 数学运算 |
| `test_sort_and_select.py` | 排序选择 | 中 | 基础功能 |
| `test_sparse.py` | 稀疏张量 | 高 | 部分功能可能不支持 |
| `test_transformers.py` | Transformer 模型 | 中 | 模型验证 |
| `test_modules.py` | 模块测试 | 中 | nn 模块扩展 |
| `nn/attention/test_*.py` | Attention 模块 | 高 | 需要 FlashAttention 支持 |
| `distributed/test_c10d.py` | 分布式通信 | 高 | 需要 HCCL 支持 |
| `distributed/tensor/` | DTensor | 高 | 分布式张量 |
| `distributed/fsdp/` | FSDP | 高 | 完全分片数据并行 |
| `npu/test_amp.py` | AMP 功能 | 低 | NPU 特有 |
| `npu/test_aclgraph_*.py` | ACL Graph | 低 | NPU 特有 |

### 4.3 低优先级迁移（可选功能）

这些测试覆盖可选或高级功能：

| 测试文件/目录 | 用途 | 迁移难度 | 说明 |
|---------------|------|----------|------|
| `test_jit.py` | JIT 编译 | 高 | 部分已同步 |
| `jit/test_*.py` | JIT 子测试 | 高 | 已同步部分 |
| `test_fx.py` | FX 中间表示 | 高 | 动态图优化 |
| `test_dynamo.py` | Dynamo | 高 | Python 编译器 |
| `inductor/test_*.py` | Inductor | 高 | 需要后端支持 |
| `test_export.py` | 导出功能 | 中 | 模型导出 |
| `profiler/test_*.py` | Profiler | 中 | 已同步部分 |
| `onnx/test_*.py` | ONNX 导出 | 高 | 已同步部分 |
| `functorch/` | functorch | 高 | 已同步部分 |
| `test_fake_tensor.py` | Fake Tensor | 中 | 元数据张量 |
| `test_functionalization.py` | Functionalization | 高 | 函数化转换 |

### 4.4 不建议迁移的测试

这些测试与 NPU 无关或依赖特定硬件：

| 测试文件/目录 | 原因 |
|---------------|------|
| `test_cuda_*.py` | CUDA 特有功能 |
| `test_metal.py` | Metal (Apple) 特有 |
| `test_nnapi.py` | NNAPI (移动端) 特有 |
| `test_mkldnn.py` | MKLDNN (Intel CPU) 特有 |
| `mobile/` | 移动端特有 |
| `test_bundled_images.py` | 图像资源测试 |
| `test_throughput_benchmark.py` | 基准测试工具 |

---

## 五、Workflow 迁移方案

### 5.1 建议创建的 Workflow

参考 XPU 测试流程，建议在 `pytorch-infra` 仓库创建：

#### `_npu-test.yml`（可复用 workflow）

```yaml
name: npu-test

on:
  workflow_call:
    inputs:
      build-environment:
        required: true
        type: string
      test-matrix:
        required: true
        type: string
      docker-image:
        required: true
        type: string
      timeout-minutes:
        required: false
        type: number
        default: 390

env:
  PYTORCH_TESTING_DEVICE_ONLY_FOR: "privateuseone"
  PYTHON_TEST_EXTRA_OPTION: "--npu"
  NO_TEST_TIMEOUT: True
```

#### `npu-test.yml`（触发 workflow）

```yaml
name: NPU Test

on:
  workflow_dispatch:
  schedule:
    - cron: '0 21 * * *'  # 每日 UTC 21:00

jobs:
  test:
    uses: ./.github/workflows/_npu-test.yml
    with:
      build-environment: linux-npu-test
      test-matrix: ${{ toJson(matrix) }}
      docker-image: npu-ci-image
```

### 5.2 建议创建的 Actions

#### `setup-npu/action.yml`

```yaml
name: Setup NPU host

runs:
  using: composite
  steps:
    - name: Check NPU availability
      shell: bash
      run: |
        # NPU-SMI 检测（如果有）
        python -c "import torch_npu; print(torch_npu.npu.device_count())"

    - name: Set GPU_FLAG for docker
      shell: bash
      run: |
        # 设置 NPU 设备访问权限
        echo "GPU_FLAG=--device=/dev/davinci0 --device=/dev/davinci_manager ..." >> "${GITHUB_ENV}"

    - name: Setup CANN environment
      shell: bash
      run: |
        # 加载 CANN 环境
        source /usr/local/Ascend/ascend-toolkit/setenv.bash
```

### 5.3 测试脚本修改建议

#### `test.sh` NPU 分支

```bash
if [[ "$BUILD_ENVIRONMENT" == *npu* ]]; then
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="privateuseone"
  export PYTHON_TEST_EXTRA_OPTION="--npu"
  export NO_TEST_TIMEOUT=True

  # CANN 环境设置
  source /usr/local/Ascend/ascend-toolkit/setenv.bash

  # NPU 设备检测
  python -c "import torch_npu; print(f'NPU count: {torch_npu.npu.device_count()}')"
fi

test_python_smoke_npu() {
  time python test/run_test.py --include test_npu test_transformers $PYTHON_TEST_EXTRA_OPTION
}
```

---

## 六、测试矩阵设计

### 6.1 测试分类

参考 PyTorch 的测试配置，建议 NPU 测试矩阵：

| 配置名 | 测试内容 | 并行度 | 超时 |
|--------|----------|--------|------|
| `default` | 核心算子测试 | 1 GPU | 240min |
| `nn` | nn 模块测试 | 1 GPU | 240min |
| `distributed` | 分布式测试 | 2-8 GPU | 390min |
| `autograd` | 自动微分测试 | 1 GPU | 240min |
| `ops` | 算子测试 | 1 GPU | 240min |
| `slow` | 慢速测试 | 1 GPU | 600min |

### 6.2 分片策略

```python
# run_test.py 分片配置
NUM_TEST_SHARDS = 8  # 根据 NPU 数量调整
SHARD_NUMBER = ${{ matrix.shard }}
```

---

## 七、持续同步机制

### 7.1 PyTorch 测试文件同步

建议定期从 PyTorch 同步测试文件：

```bash
# sync_pytorch_tests.sh
PYTORCH_REPO=/home/wangsike/workspace/pytorch/pytorch/pytorch
ASCEND_REPO=/home/wangsike/workspace/pytorch/ascend_pytorch/pytorch

# 同步测试文件
for file in $(cat testfiles_synchronized.txt); do
  cp "$PYTORCH_REPO/$file" "$ASCEND_REPO/$file"
done

# 运行适配脚本
python adapt_testcases_to_npu.py
```

### 7.2 CI 集成

建议在 `pytorch-infra` 中添加：

1. **定时同步**: 每日从 PyTorch nightly 同步测试
2. **自动适配**: 运行 `adapt_testcases_to_npu.py`
3. **增量测试**: 只测试变更的测试文件

---

## 八、风险与限制

### 8.1 数据类型限制

NPU 不完全支持的数据类型：
- `complex128` - 不支持
- `complex64` - 不支持
- `complex32` - 不支持
- `bfloat16` - 部分算子不支持
- `float64` - 部分算子不支持

### 8.2 功能限制

不完全支持的功能：
- 稀疏张量（Sparse Tensor）
- 部分 JIT 功能
- 部分 Inductor 后端
- FlashAttention（需要特定实现）

### 8.3 分布式限制

分布式测试需要：
- HCCL 通信库支持
- 多 NPU 环境
- 特定网络拓扑

---

## 九、总结

### 9.1 迁移优先级

1. **立即迁移**: 核心 NPU 功能测试（已存在）
2. **短期迁移**: 基础算子测试（已同步，需更新）
3. **中期迁移**: 分布式测试、模型测试
4. **长期迁移**: JIT、Inductor、Dynamo 高级功能

### 9.2 关键行动项

1. 创建 `_npu-test.yml` workflow
2. 创建 `setup-npu` action
3. 设计 NPU 测试矩阵
4. 建立测试文件同步机制
5. 完善 disabled_tests 配置

### 9.3 参考 XPU 成功经验

XPU 测试流程已成功集成到 PyTorch CI，可作为 NPU 迁移的最佳参考：
- 设备特定环境变量
- Docker GPU Flag 设置
- Smoke 测试验证
- 分片测试策略
- 超时配置

---

## 附录：测试文件统计

### PyTorch 测试文件数量

| 目录 | 文件数 | 说明 |
|------|--------|------|
| test/*.py | ~100 | 主测试文件 |
| test/distributed/ | ~150 | 分布式测试 |
| test/jit/ | ~80 | JIT 测试 |
| test/inductor/ | ~200 | Inductor 测试 |
| test/dynamo/ | ~50 | Dynamo 测试 |
| test/onnx/ | ~40 | ONNX 测试 |
| test/fx/ | ~20 | FX 测试 |
| test/profiler/ | ~10 | Profiler 测试 |
| test/cpp/ | ~30 | C++ 测试 |

### Ascend/pytorch 已同步文件

| 类型 | 文件数 | 来源 |
|------|--------|------|
| 主测试 | ~50 | PyTorch sync |
| NPU 特有 | ~60 | 自研 |
| JIT 子测试 | ~75 | PyTorch sync |
| ONNX 测试 | ~20 | PyTorch sync |
| Profiler | ~4 | PyTorch sync |