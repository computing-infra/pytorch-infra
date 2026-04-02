# PyTorch 测试用例指南

本文档介绍 PyTorch 测试目录结构、测试框架以及如何在不同设备上运行测试。

## 1. 测试目录概览

PyTorch 测试用例位于 `test/` 目录下，共有 **178 个 Python 测试文件**。

### 1.1 主要测试文件

| 类别 | 测试文件 | 说明 |
|------|---------|------|
| **核心测试** | `test_torch.py` | 核心 Tensor 功能 |
| | `test_autograd.py` | 自动微分 |
| | `test_nn.py` | 神经网络模块 |
| | `test_ops.py` | 算子测试 |
| | `test_native_functions.py` | 原生函数测试 |
| | `test_binary_ufuncs.py` | 二元通用函数 |
| | `test_reductions.py` | 归约操作 |
| **设备测试** | `test_cuda.py` | CUDA 专用测试 |
| | `test_mps.py` | MPS (Apple Silicon) 测试 |
| | `test_xpu.py` | Intel XPU 测试 |
| **分布式** | `distributed/test_c10d_*.py` | 分布式通信 |
| | `distributed/fsdp/` | FSDP 测试 |
| **JIT** | `jit/test_*.py` | TorchScript/JIT 测试 |
| **Inductor** | `inductor/test_torchinductor.py` | Inductor 编译器 |
| | `inductor/test_aot_inductor.py` | AOT Inductor |
| **其他** | `test_quantization.py` | 量化测试 |
| | `test_sparse.py` | 稀疏张量 |
| | `test_dataloader.py` | 数据加载器 |
| | `test_serialization.py` | 序列化 |

### 1.2 子目录结构

```
test/
├── distributed/          # 分布式测试
│   ├── fsdp/            # FSDP
│   ├── nn/              # 分布式 NN
│   ├── rpc/             # RPC
│   ├── tensor/          # 分布式张量
│   ├── test_c10d_nccl.py
│   ├── test_c10d_gloo.py
│   └── test_device_mesh.py
├── jit/                  # JIT/TorchScript
│   ├── test_tracer.py
│   ├── test_freezing.py
│   └── test_class_type.py
├── inductor/             # Inductor 编译器
│   ├── test_torchinductor.py
│   ├── test_aot_inductor.py
│   ├── test_cudagraph_trees.py
│   └── test_triton_kernels.py
├── cpp/                  # C++ 测试
│   ├── api/
│   ├── jit/
│   └── aoti_*/
├── dynamo/               # Dynamo 测试
├── fx/                   # FX 测试
├── export/               # 导出相关
├── quantization/         # 量化测试
├── mobile/               # 移动端测试
└── onnx/                 # ONNX 导出测试
```

## 2. 设备类型测试框架

PyTorch 使用 `instantiate_device_type_tests()` 框架来生成设备特定测试。这允许编写一次测试代码，自动生成适用于不同设备的测试。

### 2.1 基本用法

```python
from torch.testing._internal.common_device_type import (
    instantiate_device_type_tests,
    onlyCPU, onlyCUDA, onlyMPS, onlyXPU,
    dtypes, dtypesIfCUDA, dtypesIfCPU,
    skipCUDAIf, skipMPSIf,
)
from torch.testing._internal.common_utils import TestCase

class TestTorchDeviceType(TestCase):
    def test_something(self, device):
        """测试模板 - device 参数会自动传入"""
        x = torch.randn(3, 3, device=device)
        y = x + x
        self.assertEqual(y.shape, (3, 3))

# 实例化为 CPU、CUDA、MPS、XPU 等版本
instantiate_device_type_tests(TestTorchDeviceType, globals())
```

### 2.2 测试命名规则

原始测试 `test_something` 实例化后：

| 设备 | 测试名称 |
|-----|---------|
| CPU | `test_something_cpu` |
| CUDA | `test_something_cuda` |
| MPS | `test_something_mps` |
| XPU | `test_something_xpu` |

### 2.3 测试基类

| 基类 | 设备类型 | 说明 |
|-----|---------|------|
| `CPUTestBase` | CPU | 标准 CPU 设备 |
| `CUDATestBase` | CUDA | NVIDIA GPU |
| `MPSTestBase` | MPS | Apple Silicon GPU |
| `XPUTestBase` | XPU | Intel GPU |
| `LazyTestBase` | Lazy | Lazy Tensor |
| `HPUTestBase` | HPU | Habana GPU |
| `PrivateUse1TestBase` | privateuse1 | 自定义设备 |

## 3. 设备特定装饰器

### 3.1 限制运行设备

```python
# 只在 CPU 上运行
@onlyCPU
def test_cpu_only(self, device):
    pass

# 只在 CUDA 上运行
@onlyCUDA
def test_cuda_only(self, device):
    pass

# 只在 MPS 上运行
@onlyMPS
def test_mps_only(self, device):
    pass

# 只在 XPU 上运行
@onlyXPU
def test_xpu_only(self, device):
    pass
```

### 3.2 跳过特定设备

```python
# 条件跳过 CUDA 测试
@skipCUDAIf(True, "原因说明")
def test_skip_cuda(self, device):
    pass

# 条件跳过 MPS 测试
@skipMPSIf(True, "原因说明")
def test_skip_mps(self, device):
    pass

# 跳过 CPU 测试
@skipCPUIf(True, "原因说明")
def test_skip_cpu(self, device):
    pass
```

### 3.3 设备特定数据类型

```python
# 所有设备都测试这些类型
@dtypes(torch.float32, torch.float64)
def test_all_devices(self, device, dtype):
    pass

# 仅 CUDA 测试这些类型
@dtypesIfCUDA(torch.float16, torch.bfloat16)
def test_cuda_dtypes(self, device, dtype):
    pass

# 仅 CPU 测试这些类型
@dtypesIfCPU(torch.float32)
def test_cpu_dtypes(self, device, dtype):
    pass
```

### 3.4 多 GPU 测试

```python
# 需要至少 2 个 GPU
@deviceCountAtLeast(2)
def test_multigpu(self, devices):
    # devices 是设备列表，如 ['cuda:0', 'cuda:1']
    pass
```

### 3.5 其他常用装饰器

```python
# 需要 LAPACK
@skipCPUIfNoLapack
def test_needs_lapack(self, device):
    pass

# 需要 MKL
@skipCPUIfNoMkl
def test_needs_mkl(self, device):
    pass

# 需要 MAGMA (CUDA)
@skipCUDAIfNoMagma
def test_needs_magma(self, device):
    pass

# 跳过 ROCm
@skipCUDAIfRocm
def test_skip_rocm(self, device):
    pass

# 仅原生设备类型
@onlyNativeDeviceTypes
def test_native_only(self, device):
    pass
```

## 4. 运行测试命令

### 4.1 运行单个测试文件

```bash
# 运行整个测试文件
python test/test_torch.py

# 运行特定测试类
python test/test_torch.py TestTorch

# 运行特定测试方法
python test/test_torch.py TestTorch.test_dir
```

### 4.2 运行设备特定测试

```bash
# CPU 测试
python test/test_torch.py TestTorchDeviceType.test_something_cpu

# CUDA 测试
python test/test_torch.py TestTorchDeviceType.test_something_cuda

# MPS 测试
python test/test_torch.py TestTorchDeviceType.test_something_mps
```

### 4.3 使用 pytest 运行

```bash
# 模糊匹配测试名称
pytest test/test_torch.py -k "test_something" -v

# 运行所有 CUDA 相关测试
pytest test/test_torch.py -k "cuda" -v

# 运行特定模块
pytest test/test_nn.py -k "Conv2d" -v

# 运行慢测试
PYTORCH_TEST_WITH_SLOW=1 pytest test/test_torch.py -k "slow"
```

### 4.4 运行 CUDA 测试

```bash
# 指定 GPU
CUDA_VISIBLE_DEVICES=0 python test/test_cuda.py TestCuda.test_name

# 多 GPU 测试
CUDA_VISIBLE_DEVICES=0,1 python test/distributed/test_c10d_nccl.py
```

### 4.5 运行 MPS 测试 (macOS)

```bash
python test/test_mps.py
```

### 4.6 运行 XPU 测试

```bash
python test/test_xpu.py
```

### 4.7 运行分布式测试

```bash
# NCCL 后端
python test/distributed/test_c10d_nccl.py

# Gloo 后端
python test/distributed/test_c10d_gloo.py

# FSDP 测试
python test/distributed/fsdp/test_fsdp.py
```

## 5. 测试分片

CI 中使用分片并行执行测试，减少总耗时。

### 5.1 环境变量控制

```bash
# 运行第 1 片（共 5 片）
SHARD_NUMBER=1 NUM_TEST_SHARDS=5 python test/test_torch.py

# 运行第 2 片（共 5 片）
SHARD_NUMBER=2 NUM_TEST_SHARDS=5 python test/test_torch.py
```

### 5.2 CI 配置示例

```yaml
# .github/workflows/pull.yml 中的分片配置
test-matrix: |
  { include: [
    { config: "default", shard: 1, num_shards: 5, runner: "linux.2xlarge" },
    { config: "default", shard: 2, num_shards: 5, runner: "linux.2xlarge" },
    { config: "default", shard: 3, num_shards: 5, runner: "linux.2xlarge" },
    { config: "default", shard: 4, num_shards: 5, runner: "linux.2xlarge" },
    { config: "default", shard: 5, num_shards: 5, runner: "linux.2xlarge" },
  ]}
```

## 6. C++ 测试

### 6.1 构建后运行

```bash
# 运行 JIT 测试
./build/bin/test_jit --gtest_filter=TestSuite.TestName

# 运行 API 测试
./build/bin/test_api

# 运行自动微分测试
./build/bin/test_autograd
```

### 6.2 C++ 测试目录

```
test/cpp/
├── api/           # C++ API 测试
├── jit/           # JIT 测试
├── aoti_*/        # AOTI 测试
├── common/        # 通用测试工具
└── dist_autograd/ # 分布式自动微分
```

## 7. 关键环境变量

| 变量 | 说明 |
|-----|------|
| `CUDA_VISIBLE_DEVICES` | 指定可见 CUDA 设备 |
| `HIP_VISIBLE_DEVICES` | 指定可见 ROCm 设备 |
| `PYTORCH_TEST_WITH_SLOW=1` | 启用慢测试 |
| `PYTORCH_TEST_WITH_SLOW_GRADCHECK=1` | 启用慢梯度检查 |
| `PYTORCH_TESTING_DEVICE_ONLY_FOR=cuda` | 仅运行指定设备测试 |
| `TEST_CONFIG` | 测试配置 (default/distributed/slow) |
| `SHARD_NUMBER` | 当前分片编号 |
| `NUM_TEST_SHARDS` | 总分片数 |
| `BUILD_ENVIRONMENT` | 构建环境标识 |
| `TORCH_SHOW_CPP_STACKTRACES=1` | 显示 C++ 堆栈 |

## 8. 测试配置类型

| 配置 | 说明 | 环境变量 |
|-----|------|---------|
| `default` | 标准测试套件 | `TEST_CONFIG=default` |
| `distributed` | 分布式训练测试 | `TEST_CONFIG=distributed` |
| `slow` | 慢测试 | `TEST_CONFIG=slow`, `PYTORCH_TEST_WITH_SLOW=1` |
| `docs_test` | 文档测试 | - |
| `jit_legacy` | JIT 传统模式 | - |
| `crossref` | 交叉引用测试 | `PYTORCH_TEST_WITH_CROSSREF=1` |
| `dynamo_wrapped` | Dynamo 包装测试 | - |
| `openreg` | 开放注册测试 | - |
| `asan` | 地址消毒器测试 | `TEST_WITH_ASAN=1` |

## 9. 慢测试

慢测试列表位于 `test/slow_tests.json`，包含执行时间超过 60 秒的测试。

```bash
# 启用慢测试
PYTORCH_TEST_WITH_SLOW=1 python test/test_torch.py

# CI 中通过 slow.yml 单独运行
# 仅在 main 分支 push 或定时执行
```

## 10. 编写测试最佳实践

### 10.1 测试模板

```python
from torch.testing._internal.common_utils import TestCase, run_tests
from torch.testing._internal.common_device_type import (
    instantiate_device_type_tests,
    onlyCPU, onlyCUDA,
    dtypes,
)

class TestMyFeature(TestCase):
    """非设备相关测试"""

    def test_basic(self):
        x = torch.randn(3, 3)
        self.assertEqual(x.shape, (3, 3))


class TestMyFeatureDeviceType(TestCase):
    """设备相关测试模板"""

    def test_on_device(self, device):
        x = torch.randn(3, 3, device=device)
        self.assertTrue(x.device.type in ['cpu', 'cuda', 'mps', 'xpu'])

    @onlyCUDA
    def test_cuda_only(self, device):
        x = torch.randn(3, 3, device=device)
        self.assertEqual(x.device.type, 'cuda')

    @dtypes(torch.float32, torch.float64)
    def test_with_dtype(self, device, dtype):
        x = torch.randn(3, 3, device=device, dtype=dtype)
        self.assertEqual(x.dtype, dtype)


# 实例化设备测试
instantiate_device_type_tests(TestMyFeatureDeviceType, globals())

if __name__ == "__main__":
    run_tests()
```

### 10.2 使用 assertEqual

```python
# 张量比较
self.assertEqual(actual, expected)

# 带容差比较
self.assertEqual(actual, expected, atol=1e-5, rtol=1e-5)

# 标量比较
self.assertEqual(actual, 42)
```

### 10.3 使用 make_tensor

```python
from torch.testing import make_tensor

# 创建随机张量
x = make_tensor((3, 4), device='cuda', dtype=torch.float32)

# 需要梯度的张量
x = make_tensor((3, 4), device='cuda', dtype=torch.float32, requires_grad=True)
```

## 11. 相关文档

- [CONTRIBUTING.md](https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md) - 贡献指南
- [ aten/src/ATen/native/README.md](https://github.com/pytorch/pytorch/blob/main/aten/src/ATen/native/README.md) - 算子实现指南
- [torch.testing._internal.common_device_type](https://github.com/pytorch/pytorch/blob/main/torch/testing/_internal/common_device_type.py) - 设备测试框架源码