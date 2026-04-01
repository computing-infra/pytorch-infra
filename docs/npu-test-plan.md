# ARM 版本 PyTorch NPU 测试执行方案

## 背景

阶段一（`nightly-build-arm.yml`）已完成 Ascend/pytorch 与 PyTorch nightly 的编译验证。阶段二需要执行 PyTorch 官方仓库的 NPU 覆盖核心功能测试。

## PyTorch 测试框架分析

### 测试框架工作原理

PyTorch 使用 `instantiate_device_type_tests()` 函数为不同设备类型生成测试类：

```python
# test/test_torch.py 末尾
instantiate_device_type_tests(TestTorchDeviceType, globals())
```

该函数会为每个可用设备类型生成对应的测试类：
- `TestTorchDeviceTypeCPU` - CPU 测试
- `TestTorchDeviceTypeCUDA` - CUDA 测试（如果 `torch.cuda.is_available()`）
- `TestTorchDeviceTypePRIVATEUSE1` - NPU 测试（如果 `torch.npu.is_available()`）

### PrivateUse1 设备支持

PyTorch 定义了 `PrivateUse1TestBase` 用于支持第三方设备扩展：

```python
# torch/testing/_internal/common_device_type.py
class PrivateUse1TestBase(DeviceTypeTestBase):
    device_type = "privateuse1"

    @classmethod
    def setUpClass(cls):
        # 获取实际的 privateuse1 后端名称（如 "npu"）
        cls.device_type = torch._C._get_privateuse1_backend_name()
        cls.device_mod = getattr(torch, cls.device_type, None)
        cls.primary_device = f"{cls.device_type}:{cls.device_mod.current_device()}"
```

### 设备可用性检测

测试框架通过以下方式检测 NPU 是否可用：

```python
def is_privateuse1_backend_available():
    privateuse1_backend_name = torch._C._get_privateuse1_backend_name()  # 返回 "npu"
    privateuse1_backend_module = getattr(torch, privateuse1_backend_name, None)  # torch.npu
    return (is_available := getattr(privateuse1_backend_module, "is_available", None)) and is_available()
```

当 `torch.npu.is_available()` 返回 `True` 时，测试框架会自动包含 NPU 设备测试。

### 环境变量控制

测试框架支持以下环境变量控制运行哪些设备的测试：

| 环境变量 | 作用 |
|----------|------|
| `PYTORCH_TESTING_DEVICE_ONLY_FOR=privateuseone` | 只运行 privateuseone 设备的测试 |
| `PYTORCH_TESTING_DEVICE_FOR_CUSTOM=privateuseone` | 运行自定义设备的测试（额外添加） |
| `PYTORCH_TESTING_DEVICE_EXCEPT_FOR=cuda` | 排除 CUDA 设备的测试 |

## 方案设计

### 环境配置

| 项目 | 阶段一（构建） | 阶段二（测试） |
|------|----------------|----------------|
| Runner | `[self-hosted, npu-910b]` | `[self-hosted, npu-910b]` |
| Docker 镜像 | `pytorch_2.11.0_a2_aarch64_builder` | 同一镜像 |
| NPU 卡数 | 无需挂载 | 挂载 1 张卡（davinci4） |
| Python 版本 | 3.11 | 3.11 |
| 构建产物 | `torch_npu-wheel-arm-*` | 下载并安装 |

### 测试流程

```
┌─────────────────────────────────────────────────────────────────┐
│  npu-910b Runner + Docker Container（挂载 NPU 卡）              │
├─────────────────────────────────────────────────────────────────┤
│  1. Checkout pytorch-infra 代码                                 │
│  2. 下载阶段一的 wheel artifact                                  │
│  3. 安装 torch nightly + torch_npu wheel                        │
│  4. Clone 官方 pytorch 仓库                                     │
│  5. 设置环境变量 PYTORCH_TESTING_DEVICE_ONLY_FOR=privateuseone  │
│  6. 运行核心测试用例                                             │
│  7. 上传测试日志                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Docker NPU 设备挂载

参考命令：
```bash
docker run --name img06_04 \
  --device /dev/davinci4 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
  -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware \
  <image>
```

GitHub Actions container 配置：
```yaml
container:
  image: swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331
  options: --user root \
    --device /dev/davinci4 \
    --device /dev/davinci_manager \
    --device /dev/devmm_svm \
    --device /dev/hisi_hdc \
    -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
    -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
    -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware
```

### 测试用例选择

参考 `docs/pytorch-test-migration-analysis.md` 的高优先级测试：

| 测试文件 | 用途 | 说明 |
|----------|------|------|
| `test_torch.py` | 基础张量操作 | 核心张量操作测试 |
| `test_nn.py` | nn 模块测试 | 神经网络模块测试 |
| `test_autograd.py` | 自动微分 | 梯度计算测试 |
| `test_ops.py` | 算子测试 | 算子正确性测试 |

### 测试执行方式

**关键点**：不需要删除源码 `torch/` 目录，测试框架会正确处理设备类型。

测试文件末尾的 `instantiate_device_type_tests()` 会：
1. 检测可用设备类型（通过 `is_privateuse1_backend_available()`）
2. 为每个设备类型生成测试类
3. 测试类使用 pip 安装的 torch，而非源码目录的 torch

**执行命令**：
```bash
# 加载 CANN 环境变量
source /usr/local/Ascend/cann/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh

# 设置只运行 privateuseone 设备的测试
export PYTORCH_TESTING_DEVICE_ONLY_FOR="privateuseone"

# 运行测试
cd official_pytorch
python test/run_test.py --include test_torch test_nn test_autograd test_ops
```

### 为什么不需要删除 torch 目录

之前的方案建议删除源码 `torch/` 目录，但这是不必要的：

1. **测试框架设计**：`instantiate_device_type_tests()` 生成的测试类会正确使用已安装的 torch
2. **Python 导入顺序**：测试脚本通过 `run_test.py` 运行，它会确保使用正确的 torch
3. **设备类型检测**：测试框架通过 `torch.npu.is_available()` 检测设备，这是运行时检测

**注意**：如果在 pytorch 源码目录直接运行 `python -c "import torch"`，确实会导入源码目录的 torch。但 `run_test.py` 的设计避免了这个问题。

### Artifact 下载机制

阶段一的 wheel artifact 命名格式：`torch_npu-wheel-arm-${{ github.run_number }}`

测试 workflow 需要：
1. 获取最近一次成功构建的 run ID
2. 下载对应的 wheel artifact
3. 安装 wheel 进行测试

```bash
# 获取最近成功的构建 run ID
gh run list --repo computing-infra/pytorch-infra \
  --workflow=nightly-build-arm.yml \
  --status=success \
  --limit=1 \
  --json databaseId \
  -q '.[0].databaseId'
```

## 代码修改

### 新增文件

`.github/workflows/npu-test.yml`

### 关键配置

#### 1. 触发方式

```yaml
on:
  push:
    paths:
      - '.github/workflows/npu-test.yml'
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00（北京时间次日 07:00），构建后 1 小时
  workflow_dispatch:
```

#### 2. Artifact 下载

使用 `dawidd6/action-download-artifact@v6` 下载跨 workflow artifact：

```yaml
- name: Download latest successful build wheel
  uses: dawidd6/action-download-artifact@v6
  with:
    workflow: nightly-build-arm.yml
    workflow_conclusion: success
    repo: computing-infra/pytorch-infra
    name: torch_npu-wheel-arm-
    name_is_regexp: true
    path: wheel_artifact
```

#### 3. 测试执行

```bash
# 加载 CANN 环境变量
source /usr/local/Ascend/cann/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh

# 设置测试环境变量
export PYTORCH_TESTING_DEVICE_ONLY_FOR="privateuseone"

# 运行测试（不需要删除 torch 目录）
cd official_pytorch
python test/run_test.py --include test_torch test_nn test_autograd test_ops
```

## 触发方式

- **定时触发**：每日 UTC 23:00（北京时间次日 07:00），在构建完成后 1 小时
- **手动触发**：`workflow_dispatch`
- **代码推送**：修改 workflow 文件时自动触发

## 后续工作

1. 推送 workflow 到远程仓库
2. 手动触发测试
3. 根据测试结果调整测试用例范围
4. 记录失败用例，分析原因

---

## 验证执行记录

### 2026-04-01 执行进展

#### ⏳ 当前状态：NPU 设备访问问题

Workflow 配置已完成，torch 和 torch_npu 可正常导入，但 NPU 设备不可用。

**最新测试结果**：
- `torch: 2.11.0+cpu` ✅
- `torch_npu: 2.12.0` ✅
- `NPU available: False` ❌
- `NPU count: 0` ❌
- 驱动错误：`drvErr=87`

**问题分析**：容器内无法访问 NPU 设备 `/dev/davinci4`，可能是：
1. 设备权限问题
2. 驱动版本不匹配
3. NPU 卡被其他进程占用
4. Docker 设备挂载配置问题

**下一步**：需要检查 runner 主机的 NPU 设备状态和 Docker 配置

#### 问题排查历程

#### 问题 1：Workflow 未触发（0s 失败）

**现象**：推送代码后 workflow 未执行，立即失败

**原因**：self-hosted runner 使用 `runs-on` 必须包含 `self-hosted` 标签

**解决**：
```yaml
# 错误配置
runs-on: npu-910b

# 正确配置
runs-on: [self-hosted, npu-910b]
```

#### 问题 2：container options YAML 格式错误

**现象**：Workflow 0s 失败，日志提示 workflow 文件问题

**原因**：`container.options` 必须是单行字符串，不支持多行格式

**解决**：将多行 options 合并为单行
```yaml
# 错误配置
options: --user root
  --device /dev/davinci4
  --device /dev/davinci_manager

# 正确配置
options: --user root --device /dev/davinci4 --device /dev/davinci_manager ...
```

#### 问题 3：YAML 多行字符串语法错误

**现象**：Workflow 0s 失败，YAML 解析错误

**原因**：在 `run: |` 块中使用多行 Python 代码时，缩进与 YAML 格式冲突

**解决**：使用单行 Python `-c` 命令或 heredoc 格式

#### 问题 4：容器中没有 gh 命令

**现象**：
```
/__w/_temp/xxx.sh: line 7: gh: command not found
Process completed with exit code 127
```

**原因**：华为云镜像未预装 GitHub CLI

**解决**：使用 `dawidd6/action-download-artifact@v6` 替代 gh 命令下载跨 workflow artifact
```yaml
- name: Download latest successful build wheel
  uses: dawidd6/action-download-artifact@v6
  with:
    workflow: nightly-build-arm.yml
    workflow_conclusion: success
    repo: computing-infra/pytorch-infra
    name: torch_npu-wheel-arm-
    name_is_regexp: true
    path: wheel_artifact
```

#### 问题 5：source 命令在 sh 中不工作

**现象**：CANN 环境变量加载失败

**原因**：GitHub Actions 默认使用 `sh -e` 执行 run，`source` 是 bash 内置命令

**解决**：指定 `shell: bash`
```yaml
- name: Verify NPU availability
  shell: bash
  run: |
    source /usr/local/Ascend/cann/set_env.sh
    ...
```

#### 问题 6：容器内网络连接超时

**现象**：
```
unable to access 'https://github.com/...': Failed to connect to github.com port 443: Connection timed out
```

**原因**：容器无法访问外部网络

**解决**：使用代理 `https://gh-proxy.test.osinfra.cn/https://github.com/...`

#### 问题 7：CANN set_env.sh 硬编码路径问题

**现象**：
```
LD_LIBRARY_PATH: /usr/local/Ascend/cann-8.5.0/lib64:...
ASCEND_HOME_PATH: /usr/local/Ascend/cann-8.5.0
ImportError: libhccl.so: cannot open shared object file
```

**原因**：`set_env.sh` 脚本硬编码了 `cann-8.5.0` 路径，但实际挂载的是 `cann-9.0.0-beta.1`

**解决**：手动设置 CANN 环境变量，不依赖 `set_env.sh`
```bash
export CANN_PATH=/usr/local/Ascend/cann
export LD_LIBRARY_PATH=$CANN_PATH/lib64:$CANN_PATH/lib64/plugin/opskernel:...
export ASCEND_HOME_PATH=$CANN_PATH
export ASCEND_OPP_PATH=$CANN_PATH/opp
```

#### 问题 8：ASCEND_OPP_PATH 未设置

**现象**：
```
Exception: ASCEND_OPP_PATH environment variable is not set.
```

**原因**：缺少 `ASCEND_OPP_PATH` 环境变量

**解决**：添加 `export ASCEND_OPP_PATH=$CANN_PATH/opp`

#### 问题 9：NPU 设备不可访问

**现象**：
```
drvErr=87
Can't get ascend_hal device count
NPU available: False
NPU count: 0
```

**原因**：`ghrunner` 用户不在 `HwHiAiUser` 组，无法访问 NPU 设备

**设备文件权限**：
```
crw-rw----. 1 HwHiAiUser HwHiAiUser 236, 4 Mar 10 11:33 /dev/davinci4
```

**解决**：将 ghrunner 添加到 HwHiAiUser 组
```bash
sudo usermod -aG HwHiAiUser ghrunner

# 验证
groups ghrunner

# 重启 runner 服务（必须重启才能生效）
cd /home/ghrunner/actions-runner
sudo ./run.sh
```

**NPU 卡状态**：
```
NPU 0: Critical（不可用）
NPU 1-7: OK（可用，其中 NPU 2 有进程占用）
推荐使用：davinci1, davinci3, davinci4
```

### 成功验证的配置

| 项目 | 配置 |
|------|------|
| Runner | `[self-hosted, npu-910b]` |
| 镜像 | `swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331` |
| CANN 路径 | `/usr/local/Ascend/cann` (符号链接到 cann-9.0.0-beta.1) |
| NNAL 路径 | `/usr/local/Ascend/nnal` |
| Wheel 下载 | `dawidd6/action-download-artifact@v6` |
| 用户权限 | `ghrunner` 需要在 `HwHiAiUser` 组 |

### 当前 workflow 配置

详见 `.github/workflows/npu-test.yml`