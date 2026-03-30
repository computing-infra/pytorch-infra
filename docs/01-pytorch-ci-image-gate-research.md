# PyTorch 各硬件设备 CI 镜像和门禁方案调研报告

## 概述

本文档调研了 PyTorch 官方仓库 (`pytorch/pytorch`) 中针对不同硬件设备的 CI/CD 镜像构建和门禁方案，包括 NVIDIA CUDA、AMD ROCm、Intel XPU、ARM aarch64、IBM s390x、RISC-V 和 Apple macOS 等平台。

---

## 一、镜像总体架构

### 1.1 镜像目录结构

```
.ci/docker/
├── build.sh                    # 镜像构建入口脚本
├── README.md                   # 镜像构建说明文档
├── requirements-ci.txt         # CI依赖
├── requirements-docs.txt       # 文档依赖
├── triton_version.txt          # Triton版本
├── triton_xpu_version.txt      # Triton-XPU版本
│
├── ubuntu/                     # 通用Ubuntu镜像 (CPU/CUDA)
│   └── Dockerfile
│
├── ubuntu-rocm/                # AMD ROCm镜像
│   └── Dockerfile
│
├── ubuntu-xpu/                 # Intel XPU镜像
│   └── Dockerfile
│
├── ubuntu-cross-riscv/         # RISC-V交叉编译镜像
│   └── Dockerfile
│
├── manywheel/                  # CD构建镜像 (wheel发布)
│   ├── Dockerfile_2_28
│   ├── Dockerfile_2_28_aarch64
│   ├── Dockerfile_s390x
│   └── build.sh
│
├── almalinux/                  # AlmaLinux镜像
│   ├── Dockerfile
│   └── build.sh
│
├── linter/                     # Linter镜像
│   └── Dockerfile
│
├── linter-cuda/               # CUDA Linter镜像
│   └── Dockerfile
│
├── common/                     # 公共安装脚本
│   ├── install_base.sh
│   ├── install_cuda.sh
│   ├── install_rocm.sh
│   ├── install_xpu.sh
│   ├── install_conda.sh
│   ├── install_gcc.sh
│   ├── install_triton.sh
│   └── ...
│
└── ci_commit_pins/             # 依赖版本pin
    ├── nccl.txt
    ├── triton.txt
    ├── triton-xpu.txt
    ├── rocm-composable-kernel.txt
    └── ...
```

### 1.2 镜像构建流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           镜像构建流程                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  .github/workflows/docker-builds.yml                                        │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │ 触发条件        │    │ build.sh        │    │ 推送镜像        │          │
│  │ - PR修改        │ ─→ │ 解析配置        │ ─→ │ ECR/GHCR       │          │
│  │ - 定时(每周三)  │    │ 构建镜像        │    │                 │          │
│  │ - 手动触发      │    │ 验证版本        │    │                 │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、各硬件设备镜像详细分析

### 2.1 NVIDIA CUDA

#### 2.1.1 镜像列表

| 镜像名称 | CUDA版本 | cuDNN | Python | GCC | Ubuntu | 用途 |
|---------|---------|-------|--------|-----|--------|------|
| `pytorch-linux-jammy-cuda12.4-cudnn9-py3-gcc11` | 12.4 | 9 | 3.10 | 11 | 22.04 | 兼容性构建 |
| `pytorch-linux-jammy-cuda12.8-cudnn9-py3-gcc11` | 12.8.1 | 9 | 3.10 | 11 | 22.04 | **主力构建版本** |
| `pytorch-linux-jammy-cuda13.0-cudnn9-py3-gcc11` | 13.0.2 | 9 | 3.10 | 11 | 22.04 | 最新版本 |
| `pytorch-linux-jammy-cuda13.0-cudnn9-py3.12-gcc11-vllm` | 13.0.2 | 9 | 3.12 | 11 | 22.04 | vLLM测试 |
| `pytorch-linux-jammy-cuda13.0-cudnn9-py3-gcc11-inductor-benchmarks` | 13.0.2 | 9 | 3.10 | 11 | 22.04 | 性能基准 |
| `pytorch-linux-jammy-cuda12.8-cudnn9-py3.10-clang15` | 12.8.1 | 9 | 3.10 | Clang15 | 22.04 | Clang构建 |
| `pytorch-linux-jammy-cuda12.8-cudnn9-py3.10-linter` | 12.8.1 | 9 | 3.10 | - | 22.04 | 代码检查 |

#### 2.1.2 GPU架构对照

| 架构代号 | 计算能力 | 产品系列 | Runner | 用途 |
|--------|---------|---------|--------|------|
| sm75 | 7.5 | Tesla T4, RTX 2080 | `linux.g4dn.*` | 通用测试 |
| sm89 | 8.9 | L4, RTX 4090 | `linux.g6.*` | 主力测试 |
| sm90 | 9.0 | H100, H200 | `linux.aws.h100` | H100专用 |
| sm100 | 10.0 | B200, B100 | `linux.dgx.b200` | B200专用 |

#### 2.1.3 Workflow分类

| Workflow | 触发条件 | 测试类型 | Runner |
|----------|---------|---------|--------|
| `trunk.yml` | main/release/tag | 主构建测试 | L4/T4 |
| `pull.yml` | PR/schedule | PR验证 | L4/T4 |
| `test-h100.yml` | 每6小时/tag | H100 Smoke | H100 |
| `test-b200.yml` | 每2小时/tag | B200 Smoke | B200 |
| `h100-distributed.yml` | 每日/tag | H100分布式 | H100×8 |
| `b200-distributed.yml` | 每日/tag | B200分布式 | B200 |
| `inductor-perf-test-nightly-h100.yml` | 每日 | H100性能 | H100 |
| `inductor-perf-test-b200.yml` | 每日 | B200性能 | B200 |

#### 2.1.4 测试矩阵示例

```yaml
# trunk.yml - CUDA 12.8 构建
test-matrix: |
  { include: [
    # 默认测试 - 5分片
    { config: "default", shard: 1-5, num_shards: 5,
      runner: "linux.g6.4xlarge.experimental.nvidia.gpu" },
    # 分布式测试 - 3分片
    { config: "distributed", shard: 1-3, num_shards: 3,
      runner: "linux.g4dn.12xlarge.nvidia.gpu" },
    # PR时间基准测试
    { config: "pr_time_benchmarks", shard: 1, num_shards: 1,
      runner: "linux.g4dn.metal.nvidia.gpu" },
  ]}

# test-h100.yml - H100专用
cuda-arch-list: '9.0'
test-matrix: |
  { include: [
    { config: "smoke", shard: 1, num_shards: 1, runner: "linux.aws.h100" },
  ]}
```

---

### 2.2 AMD ROCm

#### 2.2.1 镜像列表

| 镜像名称 | ROCm版本 | Python | GCC | Ubuntu | 目标架构 | 用途 |
|---------|---------|--------|-----|--------|---------|------|
| `pytorch-linux-jammy-rocm-n-py3` | 7.2 | 3.10 | 13 | 22.04 | gfx90a;gfx942;gfx950;gfx1100 | 通用构建 |
| `pytorch-linux-noble-rocm-n-py3` | 7.2 | 3.12 | 13 | 24.04 | gfx90a;gfx942;gfx950;gfx1100 | 新版构建 |
| `pytorch-linux-noble-rocm-nightly-py3` | nightly | 3.12 | 13 | 24.04 | gfx942 | TheRock nightly |
| `pytorch-linux-jammy-rocm-n-py3-benchmarks` | 7.2 | 3.10 | 13 | 22.04 | gfx90a;gfx942;gfx950;gfx1100 | 性能基准 |

#### 2.2.2 GPU架构对照

| 架构代号 | 产品名称 | 类型 | Runner |
|--------|---------|------|--------|
| gfx90a | MI210/MI250/MI250X | CDNA 2 | `linux.rocm.gpu.2` |
| gfx942 | MI300A/MI300X | CDNA 3 | `linux.rocm.gpu.gfx942.1/4` |
| gfx950 | MI355/MI350 | CDNA 4 | `linux.rocm.gpu.gfx950.1/2` |
| gfx1100 | Radeon RX 7900 | RDNA 3 | `linux.rocm.gpu.gfx1100` |

#### 2.2.3 Workflow分类

| Workflow | 触发条件 | 测试类型 | Runner | 分片数 |
|----------|---------|---------|--------|--------|
| `rocm-mi200.yml` | 手动/tag | MI200测试 | MI210 | 6 |
| `rocm-mi300.yml` | 每3小时/tag | MI300高频测试 | MI300 | 6 |
| `rocm-mi355.yml` | 每日/tag | MI355测试 | MI355 | 6 |
| `rocm-navi31.yml` | 每2小时 | 消费级GPU测试 | RX 7900 | 2 |
| `periodic-rocm-mi300.yml` | 每3小时 | 分布式测试 | MI300×4 | 3 |
| `slow-rocm-mi200.yml` | 手动/tag | 慢速测试 | MI210 | 2 |
| `inductor-rocm-mi300.yml` | 每3小时 | Inductor测试 | MI300 | 2 |
| `inductor-perf-test-nightly-rocm-mi300.yml` | 每日 | 性能基准 | MI300 | 5-9 |

#### 2.2.4 ROCm Dockerfile 关键组件

```dockerfile
# ubuntu-rocm/Dockerfile 关键部分

# ROCm环境变量
ENV ROCM_VERSION=${ROCM_VERSION}
ENV PYTORCH_ROCM_ARCH=${PYTORCH_ROCM_ARCH}

# 安装ROCm
COPY ./common/install_rocm.sh install_rocm.sh
RUN bash ./install_rocm.sh

# 安装MAGMA (ROCm版)
COPY ./common/install_rocm_magma.sh install_rocm_magma.sh
RUN bash ./install_rocm_magma.sh ${ROCM_VERSION}

# 安装MIOpen
COPY ./common/install_miopen.sh install_miopen.sh
RUN bash ./install_miopen.sh ${ROCM_VERSION}

# 安装RCCL (分布式通信)
# 已包含在ROCm安装中

# 环境变量设置
# 写入 /etc/rocm_env.sh
```

#### 2.2.5 ROCm安装脚本关键内容

```bash
# install_rocm.sh 关键内容

function install_ubuntu() {
    # 添加ROCm仓库
    wget -qO - http://repo.radeon.com/rocm/rocm.gpg.key | apt-key add -
    echo "deb [arch=amd64] http://repo.radeon.com/rocm/apt/${ROCM_VERSION} ${UBUNTU_VERSION_NAME} main" > /etc/apt/sources.list.d/rocm.list

    # 安装ROCm组件
    apt-get install -y rocm-dev rocm-utils rocm-libs rccl rocprofiler-dev roctracer-dev amd-smi-lib

    # 安装预编译MIOpen kernels
    apt-get install -y miopen-hip-gfx*

    # 写入环境变量
    cat > /etc/rocm_env.sh << EOF
export ROCM_PATH=/opt/rocm
export ROCM_HOME=/opt/rocm
export PATH=/opt/rocm/bin:/opt/rocm/llvm/bin:$PATH
export ROCM_DEVICE_LIB_PATH=/opt/rocm/amdgcn/bitcode
export MAGMA_HOME=/opt/rocm/magma
EOF
}
```

---

### 2.3 Intel XPU

#### 2.3.1 镜像列表

| 镜像名称 | XPU版本 | Python | GCC | Ubuntu | Driver类型 | 用途 |
|---------|---------|--------|-----|--------|-----------|------|
| `pytorch-linux-jammy-xpu-n-1-py3` | 2025.2 | 3.10 | 11 | 22.04 | LTS | 旧版构建 |
| `pytorch-linux-noble-xpu-n-py3` | 2025.3 | 3.10 | 13 | 24.04 | LTS | 新版构建 |
| `pytorch-linux-noble-xpu-n-py3-client` | 2025.3 | 3.10 | 13 | 24.04 | CLIENT | Client测试 |
| `pytorch-linux-noble-xpu-n-py3-inductor-benchmarks` | 2025.3 | 3.10 | 13 | 24.04 | LTS | 性能基准 |

#### 2.3.2 XPU Dockerfile 关键组件

```dockerfile
# ubuntu-xpu/Dockerfile 关键部分

# 安装XPU依赖
ARG XPU_VERSION
ARG XPU_DRIVER_TYPE
COPY ./common/install_xpu.sh install_xpu.sh
RUN bash ./install_xpu.sh && rm install_xpu.sh

# 安装Triton-XPU
ARG TRITON
COPY ./common/install_triton.sh install_triton.sh
COPY ci_commit_pins/triton-xpu.txt triton-xpu.txt
COPY triton_xpu_version.txt triton_version.txt
RUN if [ -n "${TRITON}" ]; then bash ./install_triton.sh; fi
```

#### 2.3.3 XPU安装脚本关键内容

```bash
# install_xpu.sh 关键内容

function install_ubuntu() {
    # 添加Intel GPU仓库
    wget -qO - https://repositories.intel.com/gpu/intel-graphics.key | gpg --dearmor --output /usr/share/keyrings/intel-graphics.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu ${VERSION_CODENAME}${XPU_DRIVER_VERSION} unified" > /etc/apt/sources.list.d/intel-gpu.list

    # 安装Level Zero和驱动
    apt-get install -y xpu-smi intel-opencl-icd libze-intel-gpu1 libze-dev intel-ocloc

    # 安装oneAPI Deep Learning Essentials
    wget -qO /tmp/intel-deep-learning-essentials.sh ${XPU_PACKAGES_URL}
    /tmp/intel-deep-learning-essentials.sh -a --silent --eula accept
}

# Driver类型选择
if [[ "${XPU_DRIVER_TYPE,,}" == "lts" ]]; then
    XPU_DRIVER_VERSION="/lts/2523"  # LTS版本
fi
```

#### 2.3.4 Workflow分类

| Workflow | 触发条件 | 测试类型 | Runner | 分片数 |
|----------|---------|---------|--------|--------|
| `xpu.yml` | 每8小时(工作日)/每日(周末) | 主测试 | `linux.idc.xpu` | 6-12 |
| `inductor-perf-test-nightly-xpu.yml` | 每日 | 性能基准 | `linux.idc.xpu` | 5-6 |

#### 2.3.5 XPU测试特殊处理

```bash
# test.sh 中的XPU处理
if [[ "$BUILD_ENVIRONMENT" == *xpu* ]]; then
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="xpu"
  export PYTHON_TEST_EXTRA_OPTION="--xpu"

  # Source Intel oneAPI环境
  source /opt/intel/oneapi/setvars.sh

  # 检查XPU状态
  timeout 30 xpu-smi discovery
fi
```

---

### 2.4 ARM aarch64

#### 2.4.1 镜像列表

| 镜像名称 | Python | GCC | Ubuntu | 用途 |
|---------|--------|-----|--------|------|
| `pytorch-linux-jammy-aarch64-py3.10-gcc13` | 3.10 | 13 | 22.04 | 主构建 |
| `pytorch-linux-jammy-aarch64-py3.10-gcc13-inductor-benchmarks` | 3.10 | 13 | 22.04 | 性能基准 |

#### 2.4.2 Dockerfile 特点

```bash
# build.sh 中的aarch64配置
pytorch-linux-jammy-aarch64-py3.10-gcc13)
    ANACONDA_PYTHON_VERSION=3.10
    GCC_VERSION=13
    ACL=yes                    # Arm Compute Library
    VISION=yes
    OPENBLAS=yes
    SKIP_LLVM_SRC_BUILD_INSTALL=yes  # x86预编译LLVM不兼容
    ;;
```

#### 2.4.3 Workflow配置

```yaml
# linux-aarch64.yml
jobs:
  linux-jammy-aarch64-py3_10-build:
    runner: linux.arm64.m7g.4xlarge  # AWS Graviton
    test-matrix: |
      { include: [
        { config: "default", shard: 1-3, num_shards: 3, runner: "linux.arm64.m7g.4xlarge" },
        { config: "default", shard: 1-3, num_shards: 3, runner: "linux.arm64.m8g.4xlarge" },
      ]}
```

---

### 2.5 IBM s390x

#### 2.5.1 镜像列表

| 镜像名称 | 基础镜像 | 用途 |
|---------|---------|------|
| `pytorch/manylinuxs390x-builder:cpu-s390x` | manylinux_2_28 | Wheel构建 |

#### 2.5.2 特点

- 使用原生 s390x 硬件 (IBM Z大型机)
- 仅 CPU 构建，无 GPU
- Runner: `linux.s390x`
- 无标准门禁流程

---

### 2.6 RISC-V

#### 2.6.1 镜像配置

| 配置项 | 值 |
|-------|-----|
| 镜像名称 | `pytorch-linux-noble-riscv64-py3.12-gcc14` |
| Dockerfile | `.ci/docker/ubuntu-cross-riscv/Dockerfile` |
| 编译方式 | **交叉编译** (x86 → riscv64) |
| Runner | `linux.c7i.2xlarge` (x86实例) |
| 模拟执行 | QEMU用户态模拟 |

#### 2.6.2 Dockerfile 关键内容

```dockerfile
# ubuntu-cross-riscv/Dockerfile

FROM --platform=linux/amd64 ubuntu:${UBUNTU_VERSION}

# 交叉编译工具链
ENV CC=riscv64-linux-gnu-gcc-14
ENV CXX=riscv64-linux-gnu-g++-14
ENV QEMU_LD_PREFIX=/usr/riscv64-linux-gnu/
ENV SYSROOT=/opt/sysroot

# 安装交叉编译工具
RUN apt-get install -y gcc-14-riscv64-linux-gnu g++-14-riscv64-linux-gnu

# 交叉编译Python依赖
RUN wget Python-${PYTHON_VERSION}.tgz && \
    ./configure --host=riscv64-linux-gnu --build=x86_64-linux-gnu \
        --prefix=${SYSROOT} --enable-shared

# 安装crossenv
RUN pip install crossenv && \
    python3 -m crossenv ${SYSROOT}/bin/python3 /opt/riscv-cross-env
```

#### 2.6.3 构建特殊处理

```bash
# build.sh 中的RISC-V处理
if [[ "$BUILD_ENVIRONMENT" == *riscv64* ]]; then
  # 激活交叉编译环境
  source /opt/riscv-cross-env/bin/activate

  export CMAKE_CROSSCOMPILING=TRUE
  export CMAKE_SYSTEM_NAME=Linux
  export CMAKE_SYSTEM_PROCESSOR=riscv64

  export USE_CUDA=0
  export USE_MKLDNN=0
  export SLEEF_TARGET_EXEC_USE_QEMU=ON
fi

# QEMU模拟设置 (在runner上)
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

---

### 2.7 Apple macOS

#### 2.7.1 特点

- **无Docker镜像**，直接在macOS上构建
- Runner类型: `macos-m1-stable`, `macos-m1-14`, `macos-m2-15`, `macos-m2-26`
- 测试 MPS (Metal Performance Shaders) GPU加速

#### 2.7.2 Workflow配置

```yaml
# mac-mps.yml
jobs:
  macos-py3-arm64-build:
    uses: ./.github/workflows/_mac-build.yml
    with:
      build-environment: macos-py3-arm64
      runner-type: macos-m1-stable
      python-version: 3.12.7
      test-matrix: |
        { include: [
          { config: "test_mps", shard: 1, num_shards: 1, runner: "macos-m1-14" },
          { config: "test_mps", shard: 1, num_shards: 1, runner: "macos-m2-15" },
          { config: "test_mps", shard: 1, num_shards: 1, runner: "macos-m2-26" },
        ]}
```

---

## 三、门禁方案详细分析

### 3.1 门禁组件架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI 门禁控制架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐         │
│   │ PR/Push     │ ──→ │ job-filter.yml   │ ──→ │ 条件判断        │         │
│   │ 触发        │     │ (选择性运行job)  │     │ jobs == ''      │         │
│   └─────────────┘     └──────────────────┘     └─────────────────┘         │
│                                  │                                          │
│                                  ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │              _runner-determinator.yml                           │      │
│   │   ┌─────────────────────────────────────────────────────────┐   │      │
│   │   │  GitHub Issue: pytorch/test-infra#5132                  │   │      │
│   │   │  存储: 实验配置 + 用户 opt-in 列表                        │   │      │
│   │   └─────────────────────────────────────────────────────────┘   │      │
│   │                           │                                      │      │
│   │                           ▼                                      │      │
│   │   ┌─────────────────────────────────────────────────────────┐   │      │
│   │   │  runner_determinator.py                                  │   │      │
│   │   │  - 检查用户 opt-in/opt-out                               │   │      │
│   │   │  - 检查 rollout percentage                               │   │      │
│   │   │  - 检查 PR Label                                         │   │      │
│   │   │  - 输出: label-type, use-arc                            │   │      │
│   │   └─────────────────────────────────────────────────────────┘   │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 job-filter.yml

#### 用途
选择性运行特定的 job，通过 `jobs-to-include` 参数指定。

#### 使用方式

```yaml
# workflow_dispatch 输入
inputs:
  jobs-to-include:
    description: "Space-separated list of job display names to run"
    default: ""

# job 条件判断
if: ${{ needs.job-filter.outputs.jobs == '' ||
        contains(needs.job-filter.outputs.jobs, ' DISPLAY-NAME ') }}
```

#### 规则
- `jobs == ''` → 运行所有 jobs
- `jobs` 有值 → 只运行包含在列表中的 jobs

### 3.3 _runner-determinator.yml

#### 用途
决定使用哪种 Runner 和实验配置。

#### 配置来源
GitHub Issue: `pytorch/test-infra#5132`

#### Issue 格式示例

```yaml
experiments:
  lf:
    rollout_percent: 25    # 25% 流量使用 LF runner
    all_branches: false    # main/release 分支除外
    default: true
---

# 用户 opt-in 列表
@User1,-lf,split_build    # User1 退出 lf 实验，加入 split_build
@User2,lf                  # User2 加入 lf 实验
@User3                     # User3 无实验
```

#### 判断逻辑

```python
def get_runner_prefix(rollout_state, workflow_requestors, branch, ...):
    # 1. 检查是否例外分支
    if is_exception_branch(branch):  # main, release, nightly, landchecks
        # 默认不启用实验

    # 2. 检查用户 opt-out
    if is_user_opted_out(user, experiment_name):
        # 不启用该实验

    # 3. 检查用户 opt-in
    if is_user_opted_in(user, experiment_name):
        enabled = True

    # 4. 按比例随机启用
    elif random.uniform(0, 100) <= rollout_perc:
        enabled = True

    # 5. 返回运行器前缀
    # lf → "lf." (Linux Foundation runner)
    # arc → "mt-" (ARC runner)
    # 无实验 → "" (Meta runner)
```

### 3.4 Runner 类型对照

| label-type | Runner类型 | 说明 |
|------------|-----------|------|
| `""` | Meta Runner | 默认 Meta 内部 runner |
| `"lf."` | LF Runner | Linux Foundation runner |
| `"lf.c."` | LF Canary Runner | LF 金丝雀 runner |
| `"mt-"` | ARC Runner | OSDC ARC runner |
| `"c-mt-"` | ARC Canary Runner | ARC 金丝雀 runner |

### 3.5 PR Label 控制

| Label | 作用 |
|-------|------|
| `no-runner-experiments` | 退出所有 runner 实验，使用默认 Meta runner |

### 3.6 例外分支

以下分支默认不参与实验，除非 `all_branches: true`：

```python
def is_exception_branch(branch: str) -> bool:
    return branch.split("/", maxsplit=1)[0] in {
        "main",
        "nightly",
        "release",
        "landchecks",
    }
```

### 3.7 各架构门禁配置对比

| 架构 | job-filter | runner-determinator | PR Label控制 |
|------|------------|---------------------|--------------|
| CUDA | ✅ | ✅ | ✅ |
| ROCm | ❌ | ✅ | ✅ |
| XPU | ❌ | ✅ | ✅ |
| aarch64 | ❌ | ✅ | ✅ |
| s390x | ❌ | ❌ | ❌ |
| RISC-V | ❌ | ❌ | ❌ |
| macOS | ❌ | ✅ | ✅ |

---

## 四、关键对比总结

### 4.1 镜像对比

| 特性 | CUDA | ROCm | XPU |
|------|------|------|-----|
| 镜像版本数 | 7+ | 4 | 4 |
| SDK版本 | CUDA 12.4/12.8/13.0 | ROCm 7.2/nightly | oneAPI 2025.2/2025.3 |
| Driver类型 | - | - | LTS/CLIENT |
| 架构区分 | sm75/sm89/sm90/sm100 | gfx90a/gfx942/gfx950/gfx1100 | PVC |
| 计算库 | cuDNN, cuBLAS, NCCL | MIOpen, rocBLAS, RCCL | oneDNN, oneMKL |
| Triton支持 | ✅ Triton | ✅ Triton-ROCm | ✅ Triton-XPU |

### 4.2 Workflow对比

| 特性 | CUDA | ROCm | XPU |
|------|------|------|-----|
| 主测试频率 | 每次提交 | MI300每3小时 | 每日3次 |
| 分布式测试 | ✅ H100/B200专用 | ✅ MI300/MI355 | ❌ |
| 性能测试 | ✅ H100/B200 | ✅ MI300/MI355 | ✅ |
| Smoke测试 | ✅ | ✅ | ✅ Client |
| Windows支持 | ✅ | ❌ | ✅ |

### 4.3 Dockerfile 组件对比

| 组件 | CUDA | ROCm | XPU |
|------|------|------|-----|
| 基础镜像 | Ubuntu | Ubuntu | Ubuntu |
| Python | Conda | Conda | Conda |
| GCC | 11/Clang15 | 13 | 11/13 |
| GPU驱动安装 | install_cuda.sh | install_rocm.sh | install_xpu.sh |
| 计算库安装 | install_nccl.sh | install_miopen.sh | oneAPI bundle |
| Triton安装 | install_triton.sh | install_triton.sh | install_triton.sh |
| 监控工具 | nvidia-smi | amd-smi, rocminfo | xpu-smi |

---

## 五、结论与建议

### 5.1 镜像设计建议

1. **参考ROCm和XPU的模式**，为每种硬件架构创建专用Dockerfile
2. **使用参数化构建**，支持多版本SDK和不同Driver类型
3. **分离公共安装脚本**，便于维护和复用
4. **版本pin管理**，使用 `ci_commit_pins/` 目录管理依赖版本

### 5.2 门禁设计建议

1. **复用现有门禁组件** (`job-filter.yml`, `_runner-determinator.yml`)
2. **支持多Runner类型**，便于灰度发布和实验
3. **PR Label控制**，支持快速退出实验
4. **例外分支管理**，保证main/release分支稳定性

### 5.3 测试策略建议

1. **分片测试**，将测试分为多个shard并行执行
2. **多种测试类型**：default、distributed、smoke、slow、inductor
3. **定时触发**，高频回归测试覆盖
4. **性能基准**，持续监控性能指标

---

## 附录：参考链接

- PyTorch 官方仓库: https://github.com/pytorch/pytorch
- Docker镜像构建: `.ci/docker/README.md`
- 门禁配置Issue: https://github.com/pytorch/test-infra/issues/5132
- Runner Determinator脚本: `.github/scripts/runner_determinator.py`