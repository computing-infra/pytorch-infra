# Ascend NPU CI 镜像和门禁方案设计文档

## 概述

本文档基于 PyTorch 官方仓库中 ROCm 和 XPU 的镜像和门禁方案，为 Ascend NPU 设备设计 CI/CD 镜像构建和门禁方案。

---

## 一、镜像设计方案

### 1.1 目录结构

```
.ci/docker/
├── ubuntu-npu/
│   └── Dockerfile                    # NPU专用Dockerfile
│
├── common/
│   ├── install_npu.sh               # NPU驱动+CANN安装脚本
│   ├── install_npu_magma.sh         # NPU版MAGMA安装 (可选)
│   └── install_npu_acl.sh           # ACL库安装 (可选)
│
├── ci_commit_pins/
│   ├── ascend.txt                   # CANN版本pin
│   ├── triton-npu.txt               # Triton-NPU版本pin (如果有)
│   └── hccl.txt                     # HCCL版本pin
│
└── triton_npu_version.txt           # Triton-NPU版本号
```

### 1.2 镜像版本规划

| 镜像名称 | CANN版本 | Python | GCC | Ubuntu | Driver类型 | 用途 |
|---------|---------|--------|-----|--------|-----------|------|
| `pytorch-linux-jammy-npu-cann8.0-py3.10-gcc11` | 8.0.RC1 | 3.10 | 11 | 22.04 | LTS | 兼容性构建 |
| `pytorch-linux-noble-npu-cann8.1-py3.10-gcc13` | 8.1.0 | 3.10 | 13 | 24.04 | LTS | **主力构建版本** |
| `pytorch-linux-noble-npu-cann8.1-py3.12-gcc13` | 8.1.0 | 3.12 | 13 | 24.04 | LTS | Python 3.12支持 |
| `pytorch-linux-noble-npu-cann8.1-py3.10-gcc13-benchmarks` | 8.1.0 | 3.10 | 13 | 24.04 | LTS | 性能基准测试 |
| `pytorch-linux-noble-npu-cann-nightly-py3.10-gcc13` | nightly | 3.10 | 13 | 24.04 | RELEASE | Nightly测试 |

### 1.3 NPU架构规划

| 架构代号 | 产品名称 | 类型 | Runner建议 |
|--------|---------|------|-----------|
| Ascend910A | 910A | 训练 | `linux.npu.gpu.910a` |
| Ascend910B | 910B/B1/B2/B3/B4 | 训练 | `linux.npu.gpu.910b` |
| Ascend310P | 310P | 推理 | `linux.npu.gpu.310p` |

### 1.4 Dockerfile 设计

```dockerfile
# .ci/docker/ubuntu-npu/Dockerfile

ARG UBUNTU_VERSION
FROM ubuntu:${UBUNTU_VERSION}

ARG UBUNTU_VERSION
ENV DEBIAN_FRONTEND noninteractive

# 设置NPU目标架构
ARG NPU_ARCH
ENV NPU_ARCH ${NPU_ARCH}

# 安装基础依赖
COPY ./common/install_base.sh install_base.sh
RUN bash ./install_base.sh && rm install_base.sh

# 安装用户
COPY ./common/install_user.sh install_user.sh
RUN bash ./install_user.sh && rm install_user.sh

# 安装katex (文档)
ARG KATEX
COPY ./common/install_docs_reqs.sh install_docs_reqs.sh
RUN bash ./install_docs_reqs.sh && rm install_docs_reqs.sh

# 安装conda和Python
ARG ANACONDA_PYTHON_VERSION
ARG DOCS
ENV ANACONDA_PYTHON_VERSION=$ANACONDA_PYTHON_VERSION
ENV PATH /opt/conda/envs/py_$ANACONDA_PYTHON_VERSION/bin:/opt/conda/bin:$PATH
ENV DOCS=$DOCS
COPY requirements-ci.txt requirements-docs.txt /opt/conda/
COPY ./common/install_conda.sh install_conda.sh
COPY ./common/common_utils.sh common_utils.sh
RUN bash ./install_conda.sh && rm install_conda.sh common_utils.sh

# 安装GCC
ARG GCC_VERSION
COPY ./common/install_gcc.sh install_gcc.sh
RUN bash ./install_gcc.sh && rm install_gcc.sh

# 安装lcov (代码覆盖率)
COPY ./common/install_lcov.sh install_lcov.sh
RUN bash ./install_lcov.sh && rm install_lcov.sh

# 安装OpenSSL
COPY ./common/install_openssl.sh install_openssl.sh
RUN bash ./install_openssl.sh
ENV OPENSSL_ROOT_DIR /opt/openssl
ENV OPENSSL_DIR /opt/openssl
RUN rm install_openssl.sh

# ========== NPU核心组件安装 ==========
ARG NPU_VERSION
ARG NPU_DRIVER_TYPE
ENV NPU_VERSION=${NPU_VERSION}
ENV NPU_DRIVER_TYPE=${NPU_DRIVER_TYPE}

COPY ./common/install_npu.sh install_npu.sh
RUN bash ./install_npu.sh && rm install_npu.sh

# 安装Triton-NPU (如果有)
ARG TRITON
COPY ./common/install_triton.sh install_triton.sh
COPY ./common/common_utils.sh common_utils.sh
COPY ci_commit_pins/triton-npu.txt triton-npu.txt
COPY triton_npu_version.txt triton_version.txt
RUN if [ -n "${TRITON}" ]; then bash ./install_triton.sh; fi
RUN rm install_triton.sh common_utils.sh triton-npu.txt triton_version.txt

# 安装Vision包
ARG VISION
COPY ./common/install_vision.sh ./common/cache_vision_models.sh ./common/common_utils.sh ./
RUN if [ -n "${VISION}" ]; then bash ./install_vision.sh; fi
RUN rm install_vision.sh cache_vision_models.sh common_utils.sh
ENV INSTALLED_VISION ${VISION}

# 安装Ninja
ARG NINJA_VERSION
COPY ./common/install_ninja.sh install_ninja.sh
RUN if [ -n "${NINJA_VERSION}" ]; then bash ./install_ninja.sh; fi
RUN rm install_ninja.sh

# 安装性能基准测试依赖
ARG INDUCTOR_BENCHMARKS
COPY ./common/install_inductor_benchmark_deps.sh install_inductor_benchmark_deps.sh
COPY ./common/common_utils.sh common_utils.sh
COPY ci_commit_pins/huggingface-requirements.txt huggingface-requirements.txt
COPY ci_commit_pins/timm.txt timm.txt
COPY ci_commit_pins/torchbench.txt torchbench.txt
ENV BUILD_AOT_INDUCTOR_TEST ${INDUCTOR_BENCHMARKS}
RUN if [ -n "${INDUCTOR_BENCHMARKS}" ]; then bash ./install_inductor_benchmark_deps.sh; fi
RUN rm install_inductor_benchmark_deps.sh common_utils.sh

# 安装ccache/sccache
COPY ./common/install_cache.sh install_cache.sh
ENV PATH /opt/cache/bin:$PATH
RUN bash ./install_cache.sh && rm install_cache.sh

# 设置环境变量
ARG BUILD_ENVIRONMENT
ENV BUILD_ENVIRONMENT ${BUILD_ENVIRONMENT}

# 安装LLVM (可选)
COPY --from=pytorch/llvm:9.0.1 /opt/llvm /opt/llvm

USER jenkins
CMD ["bash"]
```

### 1.5 install_npu.sh 脚本设计

```bash
#!/bin/bash
# .ci/docker/common/install_npu.sh
#
# 参考: install_xpu.sh, install_rocm.sh

set -xe

# NPU版本映射
declare -A CANN_VERSIONS=(
    ["8.0"]="8.0.RC1"
    ["8.1"]="8.1.0"
    ["8.2"]="8.2.0"
    ["nightly"]="nightly"
)

# Driver类型
# LTS: 长期支持版本
# RELEASE: 最新发布版本

function install_ubuntu() {
    . /etc/os-release

    # 支持的Ubuntu版本
    if [[ ! " jammy noble " =~ " ${VERSION_CODENAME} " ]]; then
        echo "Ubuntu version ${VERSION_CODENAME} not supported"
        exit 1
    fi

    apt-get update -y
    apt-get install -y wget gpg-agent

    # ========== 安装NPU驱动 ==========
    if [[ "${NPU_DRIVER_TYPE,,}" == "lts" ]]; then
        # LTS驱动版本
        NPU_DRIVER_REPO="https://repo.huaweicloud.com/kunpeng-pkg/kunpeng-sc/mainline"
    else
        # RELEASE版本
        NPU_DRIVER_REPO="https://repo.huaweicloud.com/kunpeng-pkg/kunpeng-sc/release"
    fi

    # 添加华为仓库
    wget -qO - ${NPU_DRIVER_REPO}/kunpeng-sc.key | gpg --dearmor --output /usr/share/keyrings/kunpeng-sc.gpg
    echo "deb [arch=arm64 signed-by=/usr/share/keyrings/kunpeng-sc.gpg] ${NPU_DRIVER_REPO}/ubuntu ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/kunpeng-sc.list

    apt-get update

    # 安装NPU驱动和固件
    apt-get install -y \
        ascend-driver \
        ascend-firmware \
        npu-smi

    # ========== 安装CANN ==========
    if [[ "${NPU_VERSION}" == "nightly" ]]; then
        # Nightly版本安装
        CANN_URL="https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/latest/Ascend-cann-toolkit_latest_linux.arm64.run"
    else
        # 正式版本安装
        CANN_VER="${CANN_VERSIONS[${NPU_VERSION}]}"
        CANN_URL="https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/${CANN_VER}/Ascend-cann-toolkit_${CANN_VER}_linux.arm64.run"
    fi

    wget -qO /tmp/cann-toolkit.run "${CANN_URL}"
    chmod +x /tmp/cann-toolkit.run
    /tmp/cann-toolkit.run --install --install-path=/usr/local/Ascend
    rm -f /tmp/cann-toolkit.run

    # 安装HCCL (分布式通信库)
    apt-get install -y hccl

    # 安装ATB (Ascend Tensor Boost)
    apt-get install -y atb

    # ========== 设置环境变量 ==========
    cat > /etc/npu_env.sh << 'EOF'
# CANN路径
export ASCEND_HOME=/usr/local/Ascend
export ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit
export ASCEND_HOME_PATH=/usr/local/Ascend
export PATH=/usr/local/Ascend/bin:/usr/local/Ascend/compiler/ccec_compiler/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/Ascend/lib64:/usr/local/Ascend/ascend-toolkit/lib64:$LD_LIBRARY_PATH

# NPU架构
export NPU_ARCH="${NPU_ARCH}"
export ASCEND_CUSTOM_PATH=/usr/local/Ascend

# TIK编译器
export TIK_COMPILER_PATH=/usr/local/Ascend/ascend-toolkit/compiler/tikcpp
EOF

    # 追加到bashrc
    echo "source /etc/npu_env.sh" >> /etc/bash.bashrc

    # 清理
    apt-get autoclean && apt-get clean
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
}

# ========== 主入口 ==========
ID=$(grep -oP '(?<=^ID=).+' /etc/os-release | tr -d '"')
case "$ID" in
    ubuntu)
        install_ubuntu
        ;;
    *)
        echo "Unsupported OS: $ID"
        exit 1
        ;;
esac
```

### 1.6 build.sh 配置新增

```bash
# .ci/docker/build.sh 新增配置

# Dockerfile选择
if [[ "$image" == *npu* ]]; then
    DOCKERFILE="${OS}-npu/Dockerfile"
fi

# 镜像配置
case "$tag" in
    pytorch-linux-jammy-npu-cann8.0-py3.10-gcc11)
        ANACONDA_PYTHON_VERSION=3.10
        GCC_VERSION=11
        VISION=yes
        NPU_VERSION=8.0
        NPU_DRIVER_TYPE=LTS
        NPU_ARCH="Ascend910A;Ascend910B"
        NINJA_VERSION=1.9.0
        TRITON=yes  # 如果有Triton-NPU
        KATEX=yes
        ;;

    pytorch-linux-noble-npu-cann8.1-py3.10-gcc13)
        ANACONDA_PYTHON_VERSION=3.10
        GCC_VERSION=13
        VISION=yes
        NPU_VERSION=8.1
        NPU_DRIVER_TYPE=LTS
        NPU_ARCH="Ascend910A;Ascend910B;Ascend910B1;Ascend910B2;Ascend910B3;Ascend910B4"
        NINJA_VERSION=1.9.0
        TRITON=yes
        KATEX=yes
        ;;

    pytorch-linux-noble-npu-cann8.1-py3.12-gcc13)
        ANACONDA_PYTHON_VERSION=3.12
        GCC_VERSION=13
        VISION=yes
        NPU_VERSION=8.1
        NPU_DRIVER_TYPE=LTS
        NPU_ARCH="Ascend910B"
        NINJA_VERSION=1.9.0
        TRITON=yes
        ;;

    pytorch-linux-noble-npu-cann8.1-py3.10-gcc13-benchmarks)
        ANACONDA_PYTHON_VERSION=3.10
        GCC_VERSION=13
        VISION=yes
        NPU_VERSION=8.1
        NPU_DRIVER_TYPE=LTS
        NPU_ARCH="Ascend910B"
        INDUCTOR_BENCHMARKS=yes
        NINJA_VERSION=1.9.0
        TRITON=yes
        ;;

    pytorch-linux-noble-npu-cann-nightly-py3.10-gcc13)
        ANACONDA_PYTHON_VERSION=3.10
        GCC_VERSION=13
        VISION=yes
        NPU_VERSION=nightly
        NPU_DRIVER_TYPE=RELEASE
        NPU_ARCH="Ascend910B"
        NINJA_VERSION=1.9.0
        TRITON=yes
        ;;
esac

# Docker build参数
--build-arg "NPU_VERSION=${NPU_VERSION}" \
--build-arg "NPU_DRIVER_TYPE=${NPU_DRIVER_TYPE}" \
--build-arg "NPU_ARCH=${NPU_ARCH}" \
```

---

## 二、门禁方案设计

### 2.1 Workflow 设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NPU CI/CD Workflow 架构                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │ 主构建测试        │  │ 分布式测试       │  │ 性能测试          │         │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤         │
│  │ npu-910b.yml     │  │ npu-distributed  │  │ inductor-perf-*  │         │
│  │ npu-310p.yml     │  │ .yml             │  │ -nightly-npu.yml │         │
│  │                  │  │                  │  │                  │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│           │                    │                     │                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │ Smoke测试        │  │ Slow测试         │  │ Nightly构建      │         │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤         │
│  │ npu-smoke.yml    │  │ slow-npu.yml     │  │ npu-nightly.yml  │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Workflow 文件设计

#### 2.2.1 主构建测试 (npu-910b.yml)

```yaml
# .github/workflows/npu-910b.yml

name: npu-910b

on:
  push:
    branches:
      - main
      - release/*
    tags:
      - ciflow/npu-910b/*
      - ciflow/npu/*
  workflow_dispatch:
  schedule:
    - cron: 0 0,6,12,18 * * *  # 每6小时运行

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref_name }}-${{ github.ref_type == 'branch' && github.sha }}-${{ github.event_name == 'workflow_dispatch' }}-${{ github.event_name == 'schedule' }}
  cancel-in-progress: true

permissions:
  id-token: write
  contents: read
  actions: read

jobs:
  get-label-type:
    if: github.repository_owner == 'pytorch'
    name: get-label-type
    uses: pytorch/pytorch/.github/workflows/_runner-determinator.yml@main
    with:
      triggering_actor: ${{ github.triggering_actor }}
      issue_owner: ${{ github.event.pull_request.user.login || github.event.issue.user.login }}
      curr_branch: ${{ github.head_ref || github.ref_name }}
      curr_ref_type: ${{ github.ref_type }}

  target-determination:
    if: github.repository_owner == 'pytorch'
    name: before-test
    uses: ./.github/workflows/target_determination.yml

  linux-noble-npu-cann8_1-py3_10-build:
    if: github.repository_owner == 'pytorch'
    name: linux-noble-npu-cann8.1-py3.10
    uses: ./.github/workflows/_linux-build.yml
    needs: get-label-type
    with:
      runner_prefix: "${{ needs.get-label-type.outputs.label-type }}"
      build-environment: linux-noble-npu-cann8.1-py3.10-910b
      docker-image-name: ci-image:pytorch-linux-noble-npu-cann8.1-py3.10-gcc13
      runner: linux.c7i.12xlarge
      test-matrix: |
        { include: [
          { config: "default", shard: 1, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
          { config: "default", shard: 2, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
          { config: "default", shard: 3, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
          { config: "default", shard: 4, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
          { config: "default", shard: 5, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
          { config: "default", shard: 6, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
        ]}
    secrets: inherit

  linux-noble-npu-cann8_1-py3_10-test:
    permissions:
      id-token: write
      contents: read
    name: linux-noble-npu-cann8.1-py3.10
    uses: ./.github/workflows/_npu-test.yml
    needs:
      - linux-noble-npu-cann8_1-py3_10-build
      - target-determination
    with:
      build-environment: ${{ needs.linux-noble-npu-cann8_1-py3_10-build.outputs.build-environment }}
      docker-image: ${{ needs.linux-noble-npu-cann8_1-py3_10-build.outputs.docker-image }}
      test-matrix: ${{ needs.linux-noble-npu-cann8_1-py3_10-build.outputs.test-matrix }}
    secrets: inherit
```

#### 2.2.2 分布式测试 (npu-distributed.yml)

```yaml
# .github/workflows/npu-distributed.yml

name: npu-distributed

on:
  schedule:
    - cron: 0 4,16 * * *  # 每日两次
  push:
    tags:
      - ciflow/npu-distributed/*
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}-${{ github.event_name == 'workflow_dispatch' }}-${{ github.event_name == 'schedule' }}
  cancel-in-progress: true

permissions:
  id-token: write
  contents: read
  actions: read

jobs:
  get-label-type:
    if: github.repository_owner == 'pytorch'
    name: get-label-type
    uses: pytorch/pytorch/.github/workflows/_runner-determinator.yml@main
    with:
      triggering_actor: ${{ github.triggering_actor }}
      issue_owner: ${{ github.event.pull_request.user.login || github.event.issue.user.login }}
      curr_branch: ${{ github.head_ref || github.ref_name }}
      curr_ref_type: ${{ github.ref_type }}

  linux-noble-npu-cann8_1-py3_10-dist-build:
    name: linux-noble-npu-cann8.1-py3.10-dist
    uses: ./.github/workflows/_linux-build.yml
    needs: get-label-type
    with:
      runner_prefix: "${{ needs.get-label-type.outputs.label-type }}"
      build-environment: linux-noble-npu-cann8.1-py3.10-910b-dist
      docker-image-name: ci-image:pytorch-linux-noble-npu-cann8.1-py3.10-gcc13
      test-matrix: |
        { include: [
          { config: "distributed", shard: 1, num_shards: 3, runner: "linux.npu.gpu.910b.4" },
          { config: "distributed", shard: 2, num_shards: 3, runner: "linux.npu.gpu.910b.4" },
          { config: "distributed", shard: 3, num_shards: 3, runner: "linux.npu.gpu.910b.4" },
        ]}
    secrets: inherit

  linux-noble-npu-cann8_1-py3_10-dist-test:
    name: linux-noble-npu-cann8.1-py3.10-dist
    uses: ./.github/workflows/_npu-test.yml
    needs: linux-noble-npu-cann8_1-py3_10-dist-build
    with:
      build-environment: ${{ needs.linux-noble-npu-cann8_1-py3_10-dist-build.outputs.build-environment }}
      docker-image: ${{ needs.linux-noble-npu-cann8_1-py3_10-dist-build.outputs.docker-image }}
      test-matrix: ${{ needs.linux-noble-npu-cann8_1-py3_10-dist-build.outputs.test-matrix }}
    secrets: inherit
```

#### 2.2.3 性能基准测试 (inductor-perf-test-nightly-npu.yml)

```yaml
# .github/workflows/inductor-perf-test-nightly-npu.yml

name: inductor-perf-nightly-npu

on:
  schedule:
    - cron: 15 0 * * *  # 每日
  workflow_dispatch:
    inputs:
      training:
        description: Run training?
        type: boolean
        default: true
      inference:
        description: Run inference?
        type: boolean
        default: true
      cudagraphs:
        description: Run with cudagraphs?
        type: boolean
        default: true
      benchmark_configs:
        description: Benchmark configs
        type: string
        default: inductor_huggingface_perf_npu,inductor_timm_perf_npu,inductor_torchbench_perf_npu

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}-${{ github.event_name == 'workflow_dispatch' }}-${{ github.event_name == 'schedule' }}
  cancel-in-progress: true

permissions: read-all

jobs:
  get-label-type:
    name: get-label-type
    uses: pytorch/pytorch/.github/workflows/_runner-determinator.yml@main
    with:
      triggering_actor: ${{ github.triggering_actor }}
      issue_owner: ${{ github.event.pull_request.user.login || github.event.issue.user.login }}
      curr_branch: ${{ github.head_ref || github.ref_name }}
      curr_ref_type: ${{ github.ref_type }}

  linux-noble-npu-cann8_1-py3_10-benchmark-build:
    name: linux-noble-npu-cann8.1-py3.10-benchmark
    uses: ./.github/workflows/_linux-build.yml
    needs: get-label-type
    with:
      runner_prefix: "${{ needs.get-label-type.outputs.label-type }}"
      build-environment: linux-noble-npu-cann8.1-py3.10-910b-benchmarks
      docker-image-name: ci-image:pytorch-linux-noble-npu-cann8.1-py3.10-gcc13-benchmarks
      test-matrix: |
        { include: [
          { config: "inductor_huggingface_perf_npu", shard: 1, num_shards: 5, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_huggingface_perf_npu", shard: 2, num_shards: 5, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_huggingface_perf_npu", shard: 3, num_shards: 5, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_huggingface_perf_npu", shard: 4, num_shards: 5, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_huggingface_perf_npu", shard: 5, num_shards: 5, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 1, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 2, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 3, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 4, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 5, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 6, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_timm_perf_npu", shard: 7, num_shards: 7, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 1, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 2, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 3, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 4, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 5, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 6, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 7, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 8, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
          { config: "inductor_torchbench_perf_npu", shard: 9, num_shards: 9, runner: "linux.npu.gpu.910b.1" },
        ]}
    secrets: inherit

  linux-noble-npu-cann8_1-py3_10-benchmark-test:
    permissions:
      id-token: write
      contents: read
    name: linux-noble-npu-cann8.1-py3.10-benchmark
    uses: ./.github/workflows/_npu-test.yml
    needs: linux-noble-npu-cann8_1-py3_10-benchmark-build
    with:
      build-environment: ${{ needs.linux-noble-npu-cann8_1-py3_10-benchmark-build.outputs.build-environment }}
      docker-image: ${{ needs.linux-noble-npu-cann8_1-py3_10-benchmark-build.outputs.docker-image }}
      test-matrix: ${{ needs.linux-noble-npu-cann8_1-py3_10-benchmark-build.outputs.test-matrix }}
      timeout-minutes: 720
      disable-monitor: true
    secrets: inherit
```

### 2.3 测试Workflow (_npu-test.yml)

```yaml
# .github/workflows/_npu-test.yml
# 参考: _rocm-test.yml, _xpu-test.yml

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
        default: 300
      disable-monitor:
        required: false
        type: boolean
        default: true
    secrets:
      HUGGING_FACE_HUB_TOKEN:
        required: false

env:
  GIT_DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}

permissions:
  id-token: write
  contents: read

jobs:
  test:
    if: github.repository_owner == 'pytorch' && toJSON(fromJSON(inputs.test-matrix).include) != '[]'
    strategy:
      matrix: ${{ fromJSON(inputs.test-matrix) }}
      fail-fast: false
    runs-on: ${{ matrix.runner }}
    timeout-minutes: ${{ inputs.timeout-minutes }}
    steps:
      - name: Checkout PyTorch
        uses: pytorch/pytorch/.github/actions/checkout-pytorch@main

      - name: Setup NPU
        uses: ./.github/actions/setup-npu

      - name: Runner check NPU count (distributed jobs)
        if: ${{ contains(matrix.config, 'distributed') }}
        shell: bash
        run: |
          nnpu=$(npu-smi info | grep -c "Ascend")
          if [[ $nnpu -lt 2 ]]; then
            echo "Error: only $nnpu NPU(s) detected, at least 2 NPUs are needed for distributed jobs"
            exit 1
          fi

      - name: Calculate docker image
        id: calculate-docker-image
        uses: pytorch/test-infra/.github/actions/calculate-docker-image@main
        with:
          docker-image-name: ${{ inputs.docker-image }}

      - name: Pull docker image
        uses: pytorch/test-infra/.github/actions/pull-docker-image@main
        with:
          docker-image: ${{ steps.calculate-docker-image.outputs.docker-image }}

      - name: Download build artifacts
        uses: ./.github/actions/download-build-artifacts
        with:
          name: ${{ inputs.build-environment }}

      - name: Parse ref
        id: parse-ref
        run: .github/scripts/parse_ref.py

      - name: Test
        id: test
        env:
          BUILD_ENVIRONMENT: ${{ inputs.build-environment }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          TEST_CONFIG: ${{ matrix.config }}
          SHARD_NUMBER: ${{ matrix.shard }}
          NUM_TEST_SHARDS: ${{ matrix.num_shards }}
          DOCKER_IMAGE: ${{ inputs.docker-image }}
          HUGGING_FACE_HUB_TOKEN: ${{ secrets.HUGGING_FACE_HUB_TOKEN }}
        run: |
          set -x

          if [[ $TEST_CONFIG == 'multigpu' ]]; then
            TEST_COMMAND=.ci/pytorch/multigpu-test.sh
          else
            TEST_COMMAND=.ci/pytorch/test.sh
          fi

          # 启动Docker容器
          container_name=$(docker run \
            -e BUILD_ENVIRONMENT \
            -e PR_NUMBER \
            -e GITHUB_ACTIONS \
            -e SHARD_NUMBER \
            -e TEST_CONFIG \
            -e NUM_TEST_SHARDS \
            -e HUGGING_FACE_HUB_TOKEN \
            --ulimit stack=10485760:83886080 \
            --ulimit core=0 \
            --security-opt seccomp=unconfined \
            --cap-add=SYS_PTRACE \
            --shm-size="8g" \
            --tty \
            --detach \
            --name="${container_name}" \
            --user jenkins \
            --privileged \
            --device=/dev/davinci0 \
            --device=/dev/davinci_manager \
            --device=/dev/devmm_svm \
            --device=/dev/hisi_hdc \
            -v "${GITHUB_WORKSPACE}:/var/lib/jenkins/workspace" \
            -w /var/lib/jenkins/workspace \
            "${DOCKER_IMAGE}"
          )

          echo "CONTAINER_NAME=${container_name}" >> "$GITHUB_ENV"

          # 执行测试
          docker exec -t "${container_name}" sh -c "cd .. && cp -R workspace pytorch && cd pytorch && pip install dist/*.whl && ${TEST_COMMAND}"

      - name: Save test results
        if: always()
        run: |
          docker exec -t "${{ env.CONTAINER_NAME }}" sh -c "cd ../pytorch && sudo cp -R test/test-reports ../workspace/test"

      - name: Upload test artifacts
        uses: ./.github/actions/upload-test-artifacts
        if: always()
        with:
          use-gha: true
          file-suffix: ${{ github.job }}-${{ matrix.config }}-${{ matrix.shard }}-${{ matrix.num_shards }}

      - name: Teardown NPU
        if: always()
        uses: ./.github/actions/teardown-npu
```

### 2.4 Setup NPU Action

```yaml
# .github/actions/setup-npu/action.yml

name: 'Setup NPU'
description: 'Setup NPU environment for CI'

runs:
  using: 'composite'
  steps:
    - name: Setup NPU environment
      shell: bash
      run: |
        # 检查NPU设备
        echo "Checking NPU devices..."
        npu-smi info

        # 设置环境变量
        if [ -f /usr/local/Ascend/bin/setenv.bash ]; then
          source /usr/local/Ascend/bin/setenv.bash
        fi

        # 检查CANN版本
        echo "CANN version:"
        cat /usr/local/Ascend/version.info 2>/dev/null || echo "Version info not found"

        # 设置Docker权限
        sudo chmod 666 /dev/davinci* 2>/dev/null || true
        sudo chmod 666 /dev/davinci_manager 2>/dev/null || true
        sudo chmod 666 /dev/devmm_svm 2>/dev/null || true
        sudo chmod 666 /dev/hisi_hdc 2>/dev/null || true
```

### 2.5 test.sh NPU处理

```bash
# .ci/pytorch/test.sh 中新增NPU处理

# NPU相关环境变量设置
if [[ "$BUILD_ENVIRONMENT" == *npu* ]]; then
  # 激活NPU环境
  if [ -f /usr/local/Ascend/bin/setenv.bash ]; then
    source /usr/local/Ascend/bin/setenv.bash
  fi

  # 设置测试设备
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="npu"
  export PYTHON_TEST_EXTRA_OPTION="--npu"

  # 检查NPU状态
  echo "Checking NPU status..."
  npu-smi info

  # 设置NPU架构
  if [ -n "$NPU_ARCH" ]; then
    echo "NPU_ARCH: $NPU_ARCH"
  fi
fi

# 测试函数
test_python_smoke_npu() {
  # NPU Smoke测试
  pytest test/npu \
    -k 'npu' \
    --npu \
    --ignore-glob='*_distributed_*' \
    ...
}

test_npu_bin() {
  # NPU二进制测试
  for npu_case in "${BUILD_BIN_DIR}"/*npu*; do
    if [[ "$npu_case" != *"*"* && "$npu_case" != *.so && "$npu_case" != *.a ]]; then
      case_name=$(basename "$npu_case")
      "$npu_case" --gtest_output=xml:"$TEST_REPORTS_DIR"/"$case_name".xml
    fi
  done
}
```

---

## 三、Runner 规划

### 3.1 Runner命名规范

```
linux.npu.gpu.<arch>.<count>

示例:
- linux.npu.gpu.910a.1    # 单卡910A
- linux.npu.gpu.910b.1    # 单卡910B
- linux.npu.gpu.910b.2    # 双卡910B
- linux.npu.gpu.910b.4    # 4卡910B
- linux.npu.gpu.910b.8    # 8卡910B
- linux.npu.gpu.310p.1    # 单卡310P
```

### 3.2 Runner资源配置

| Runner类型 | NPU数量 | CPU | 内存 | 用途 |
|-----------|--------|-----|------|------|
| `linux.npu.gpu.910b.1` | 1 | 32核 | 64GB | 默认测试 |
| `linux.npu.gpu.910b.2` | 2 | 64核 | 128GB | 分布式测试 |
| `linux.npu.gpu.910b.4` | 4 | 128核 | 256GB | 分布式测试 |
| `linux.npu.gpu.910b.8` | 8 | 256核 | 512GB | 大规模分布式 |

---

## 四、docker-builds.yml 更新

```yaml
# .github/workflows/docker-builds.yml 更新

jobs:
  docker-build:
    strategy:
      matrix:
        docker-image-name: [
          # ... 现有镜像 ...
          pytorch-linux-jammy-npu-cann8.0-py3.10-gcc11,
          pytorch-linux-noble-npu-cann8.1-py3.10-gcc13,
          pytorch-linux-noble-npu-cann8.1-py3.12-gcc13,
          pytorch-linux-noble-npu-cann8.1-py3.10-gcc13-benchmarks,
          pytorch-linux-noble-npu-cann-nightly-py3.10-gcc13,
        ]
```

---

## 五、环境变量对照表

| CUDA | ROCm | XPU | **NPU (Ascend)** |
|------|------|-----|------------------|
| `CUDA_VERSION` | `ROCM_VERSION` | `XPU_VERSION` | `NPU_VERSION` (CANN版本) |
| `CUDA_PATH` | `ROCM_HOME` | - | `ASCEND_HOME` |
| `CUDA_HOME` | `ROCM_PATH` | - | `ASCEND_TOOLKIT_HOME` |
| `LD_LIBRARY_PATH` (cuda) | `LD_LIBRARY_PATH` (rocm) | - | `LD_LIBRARY_PATH` (ascend) |
| - | `PYTORCH_ROCM_ARCH` | - | `NPU_ARCH` / `PYTORCH_NPU_ARCH` |
| NCCL | RCCL | - | HCCL |
| cuDNN | MIOpen | oneDNN | ACL (Ascend Computing Library) |
| nvcc | hipcc | icx | ascend compiler |
| nvidia-smi | amd-smi, rocminfo | xpu-smi | npu-smi |

---

## 六、实施计划

### 阶段一：基础镜像构建 (Week 1-2)

1. 创建 `ubuntu-npu/Dockerfile`
2. 创建 `common/install_npu.sh`
3. 更新 `build.sh` 配置
4. 测试镜像构建

### 阶段二：CI Workflow 配置 (Week 3-4)

1. 创建 `_npu-test.yml`
2. 创建 `npu-910b.yml`
3. 创建 Setup/Teardown Actions
4. 更新 `test.sh` NPU处理

### 阶段三：高级功能 (Week 5-6)

1. 分布式测试 Workflow
2. 性能基准测试 Workflow
3. Nightly构建 Workflow
4. 监控和告警配置

### 阶段四：门禁集成 (Week 7)

1. 集成 `_runner-determinator.yml`
2. 配置 PR Label 控制
3. 灰度发布配置

---

## 七、参考资源

- PyTorch ROCm镜像: `.ci/docker/ubuntu-rocm/`
- PyTorch XPU镜像: `.ci/docker/ubuntu-xpu/`
- CANN文档: https://www.hiascend.com/document
- HCCL文档: https://www.hiascend.com/document/detail/zh/canncommercial/700/featureintro/HCCLfeatureintro/HCCL_01_0001.html
- npu-smi工具: https://www.hiascend.com/document/detail/zh/canncommercial/700/tools/npusmi/npusmi_01_0001.html

---

## 八、NPU 测试用例设计

### 8.1 设备无关测试框架概述

PyTorch 提供了 `instantiate_device_type_tests` 机制，允许同一测试模板为不同设备类型实例化测试。这是实现设备无关测试的核心机制。

```python
# torch/testing/_internal/common_device_type.py

# 设备测试基类
class DeviceTypeTestBase(TestCase):
    device_type: str = "generic_device_type"

# 设备测试基类列表
device_type_test_bases = [CPUTestBase, CUDATestBase, XPUTestBase, MPSTestBase, ...]
```

#### 环境变量控制

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `PYTORCH_TESTING_DEVICE_ONLY_FOR` | 仅运行指定设备的测试 | `npu` 或 `npu,cpu` |
| `PYTORCH_TESTING_DEVICE_EXCEPT_FOR` | 排除指定设备的测试 | `cuda,xpu` |
| `TORCH_TEST_DEVICES` | 自定义测试设备路径 | `/path/to/npu_test_base.py` |

### 8.2 设备无关测试用例列表

以下测试文件使用 `instantiate_device_type_tests`，可在 CPU、CUDA、XPU、NPU 等设备上运行：

#### 8.2.1 核心运算测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `test_ops.py` | 算子测试 (OpInfo) | ✅ 使用 `instantiate_device_type_tests` |
| `test_ops_gradients.py` | 算子梯度测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_ops_fwd_gradients.py` | 前向梯度测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_prims.py` | 原语算子测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_reductions.py` | 归约操作测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_view_ops.py` | 视图操作测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_unary_ufuncs.py` | 一元通用函数测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_binary_ufuncs.py` | 二元通用函数测试 | ✅ 通过 run_test.py |
| `test_indexing.py` | 索引操作测试 | ✅ 通过 run_test.py |
| `test_scatter_gather_ops.py` | 散射/聚集操作测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_tensor_creation_ops.py` | 张量创建操作测试 | ✅ 使用 `instantiate_device_type_tests` |

#### 8.2.2 数学运算测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `test_linalg.py` | 线性代数测试 | ✅ 通过 run_test.py |
| `test_spectral_ops.py` | 频谱操作测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_segment_reductions.py` | 分段归约测试 | ✅ 通过 run_test.py |
| `test_complex.py` | 复数运算测试 | ✅ 通过 run_test.py |

#### 8.2.3 张量特性测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `test_sparse.py` | 稀疏张量测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_sparse_csr.py` | CSR稀疏张量测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_nestedtensor.py` | 嵌套张量测试 | ✅ 通过 run_test.py |
| `test_namedtensor.py` | 命名张量测试 | ✅ 通过 run_test.py |
| `test_fake_tensor.py` | FakeTensor测试 | ✅ 通过 run_test.py |

#### 8.2.4 自动求导测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `test_autograd.py` | 自动求导核心测试 | ✅ 通过 run_test.py |
| `test_functionalization.py` | 函数化测试 | ✅ 通过 run_test.py |
| `test_expanded_weights.py` | 扩展权重测试 | ✅ 通过 run_test.py |

#### 8.2.5 神经网络测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `test_nn.py` | 神经网络模块测试 | ✅ 通过 run_test.py |
| `test_modules.py` | 模块测试 | ✅ 通过 run_test.py |
| `test_optim.py` | 优化器测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_transformers.py` | Transformer相关测试 | ✅ 使用 `instantiate_device_type_tests` |

#### 8.2.6 编译器/Inductor测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `inductor/test_torchinductor.py` | Inductor核心测试 | ✅ 支持多设备 |
| `inductor/test_aot_inductor.py` | AOT Inductor测试 | ✅ 支持多设备 |
| `test_decomp.py` | 分解规则测试 | ✅ 通过 run_test.py |
| `test_dispatch.py` | 分发机制测试 | ✅ 通过 run_test.py |

#### 8.2.7 其他通用测试

| 测试文件 | 测试内容 | 设备无关性 |
|---------|---------|-----------|
| `test_torch.py` | PyTorch核心功能测试 | ✅ 通过 run_test.py |
| `test_serialization.py` | 序列化测试 | ✅ 通过 run_test.py |
| `test_dataloader.py` | 数据加载器测试 | ✅ 通过 run_test.py |
| `test_utils.py` | 工具函数测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_type_promotion.py` | 类型提升测试 | ✅ 使用 `instantiate_device_type_tests` |
| `test_testing.py` | 测试框架测试 | ✅ 使用 `instantiate_device_type_tests` |

### 8.3 NPU 测试配置

#### 8.3.1 run_test.py 配置新增

```python
# test/run_test.py 新增配置

# NPU 特有测试
NPU_TEST = [
    "test_npu",
]

# NPU 需要跳过的测试 (待完善)
NPU_BLOCKLIST = [
    # 根据 Ascend/pytorch 实际情况补充
    # "test_autograd",  # 示例：如果 autograd 某些功能不支持
]

# XPU_BLOCKLIST 作为参考
XPU_BLOCKLIST = [
    "test_autograd",
    "profiler/test_memory_profiler",
]
```

#### 8.3.2 test.sh NPU 处理

```bash
# .ci/pytorch/test.sh 新增 NPU 处理

if [[ "$BUILD_ENVIRONMENT" == *npu* ]]; then
  export PYTORCH_TESTING_DEVICE_ONLY_FOR="npu"
  export PYTHON_TEST_EXTRA_OPTION="--npu"

  # 激活 NPU 环境
  if [ -f /usr/local/Ascend/bin/setenv.bash ]; then
    source /usr/local/Ascend/bin/setenv.bash
  fi

  # 检查 NPU 状态
  echo "Checking NPU status..."
  npu-smi info

  # 设置 NPU 架构
  if [ -n "$NPU_ARCH" ]; then
    echo "NPU_ARCH: $NPU_ARCH"
  fi
fi

# NPU Smoke 测试函数
test_python_smoke_npu() {
  # NPU Smoke 测试
  python test/run_test.py --include test_transformers $PYTHON_TEST_EXTRA_OPTION --upload-artifacts-while-running
  assert_git_not_dirty
}

# NPU 二进制测试函数
test_npu_bin() {
  # 运行 NPU 特有的二进制测试
  for npu_case in "${BUILD_BIN_DIR}"/*npu*; do
    if [[ "$npu_case" != *"*"* && "$npu_case" != *.so && "$npu_case" != *.a ]]; then
      case_name=$(basename "$npu_case")
      "$npu_case" --gtest_output=xml:"$TEST_REPORTS_DIR"/"$case_name".xml
    fi
  done
}
```

#### 8.3.3 run_test.py 参数新增

```python
# test/run_test.py 新增 --npu 参数

parser.add_argument(
    "--npu",
    "--npu",
    action="store_true",
    help=("If this flag is present, we will run npu tests except NPU_BLOCK_LIST"),
)

# NPU 测试选择逻辑
if options.npu:
    selected_tests = exclude_tests(NPU_BLOCKLIST, selected_tests, "on NPU")
else:
    # 排除 NPU 特有测试
    options.exclude.extend(NPU_TEST)
```

### 8.4 NPU 测试基类设计

参考 `XPUTestBase` 和 `PrivateUse1TestBase`，设计 NPU 测试基类：

```python
# torch_npu/testing/_internal/test_base.py

import torch
from torch.testing._internal.common_device_type import DeviceTypeTestBase

class NPUTestBase(DeviceTypeTestBase):
    device_type = "npu"

    @classmethod
    def setUpClass(cls):
        if not torch.npu.is_available():
            raise unittest.SkipTest("NPU not available")
        cls.primary_device = f"npu:{torch.npu.current_device()}"
        cls.device_mod = torch.npu

    @classmethod
    def instantiate_test(cls, name, test, generic_cls=None):
        # 实例化测试
        return super().instantiate_test(name, test, generic_cls)
```

### 8.5 测试分类策略

#### 8.5.1 按测试类型分类

| 测试类型 | 说明 | 示例测试 |
|---------|------|---------|
| **Smoke 测试** | 快速验证核心功能 | `test_transformers`, `test_ops` |
| **Default 测试** | 默认测试集 | 分片运行所有设备无关测试 |
| **Distributed 测试** | 分布式相关测试 | `distributed/test_c10d*`, `distributed/tensor/*` |
| **Slow 测试** | 耗时较长的测试 | `test_jit`, `test_nn` (slow模式) |
| **Inductor 测试** | 编译器相关测试 | `inductor/test_torchinductor*` |

#### 8.5.2 按测试优先级分类

| 优先级 | 测试类型 | 运行频率 |
|-------|---------|---------|
| P0 | Smoke 测试 | 每次提交 |
| P1 | Default 测试 | 每次提交 |
| P2 | Distributed 测试 | 每日 |
| P3 | Slow 测试 | 每周 |
| P4 | 性能基准测试 | 每日 |

### 8.6 测试矩阵配置

#### 8.6.1 默认测试矩阵

```yaml
# npu-910b.yml 测试矩阵
test-matrix: |
  { include: [
    # Default 测试 - 6分片
    { config: "default", shard: 1, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
    { config: "default", shard: 2, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
    { config: "default", shard: 3, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
    { config: "default", shard: 4, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
    { config: "default", shard: 5, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
    { config: "default", shard: 6, num_shards: 6, runner: "linux.npu.gpu.910b.1" },
  ]}
```

#### 8.6.2 分布式测试矩阵

```yaml
# npu-distributed.yml 测试矩阵
test-matrix: |
  { include: [
    { config: "distributed", shard: 1, num_shards: 3, runner: "linux.npu.gpu.910b.4" },
    { config: "distributed", shard: 2, num_shards: 3, runner: "linux.npu.gpu.910b.4" },
    { config: "distributed", shard: 3, num_shards: 3, runner: "linux.npu.gpu.910b.4" },
  ]}
```

### 8.7 NPU 特有测试用例

以下测试用例需要在 NPU 设备上运行，用于验证 NPU 特有功能：

| 测试文件 | 测试内容 | 备注 |
|---------|---------|------|
| `test_npu.py` | NPU 核心功能测试 | 类似 `test_xpu.py` |
| `npu/test_custom_op.py` | NPU 自定义算子测试 | NPU 特有算子 |
| `npu/test_aclnn.py` | ACL NN 算子测试 | CANN 算子封装 |
| `npu/test_hccl.py` | HCCL 通信测试 | 分布式通信 |
| `npu/test_graph_mode.py` | 图模式测试 | NPU 图执行模式 |

### 8.8 测试排除列表 (Blocklist)

根据 XPU 和 ROCm 的经验，NPU 可能需要在以下测试中进行适配：

```python
# test/run_test.py

NPU_BLOCKLIST = [
    # 自动求导相关 (部分功能可能不支持)
    # "test_autograd",

    # Profiler 相关 (NPU profiler 实现可能不同)
    # "profiler/test_memory_profiler",

    # CUDA 特有测试 (不应在 NPU 上运行)
    "test_cuda",
    "test_cuda_multigpu",
    "test_cuda_primary_ctx",
    "test_cuda_sanitizer",
    "test_matmul_cuda",
    "test_scaled_matmul_cuda",

    # XPU 特有测试
    "test_xpu",

    # MPS 特有测试
    "test_mps",
    "test_metal",
]
```

### 8.9 测试环境变量汇总

```bash
# NPU 测试环境变量

# 设备类型
export PYTORCH_TESTING_DEVICE_ONLY_FOR="npu"

# 测试配置
export TEST_CONFIG="default"  # 或 "distributed", "slow", "smoke_npu"

# 构建环境
export BUILD_ENVIRONMENT="linux-noble-npu-cann8.1-py3.10-910b"

# NPU 架构
export NPU_ARCH="Ascend910B"

# CANN 路径
export ASCEND_HOME=/usr/local/Ascend
export ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit

# HCCL 配置 (分布式测试)
export HCCL_CONNECT_TIMEOUT=7200
export HCCL_EXEC_TIMEOUT=0
```

### 8.10 与其他设备测试对比

| 特性 | CUDA | ROCm | XPU | **NPU** |
|------|------|------|-----|---------|
| Smoke 测试 | ✅ H100/B200 | ✅ MI300 | ✅ Client | ✅ 910B |
| Default 测试 | ✅ 5-6分片 | ✅ 6分片 | ✅ 6-12分片 | ✅ 6分片 |
| Distributed 测试 | ✅ H100×8 | ✅ MI300×4 | ❌ | ✅ 910B×4 |
| Inductor 测试 | ✅ | ✅ | ✅ | ✅ |
| 性能基准测试 | ✅ H100/B200 | ✅ MI300 | ✅ | ✅ 910B |
| Slow 测试 | ✅ | ✅ | ❌ | ✅ |

### 8.11 测试实施建议

1. **阶段一：Smoke 测试** - 优先实现 `test_transformers` 等核心测试
2. **阶段二：Default 测试** - 逐步覆盖所有设备无关测试
3. **阶段三：分布式测试** - 实现 HCCL 分布式通信测试
4. **阶段四：性能测试** - 实现 Inductor 性能基准测试
5. **持续完善** - 根据测试结果调整 blocklist

---

## 九、扩展机制

### 9.1 添加新设备类型

参考 PyTorch 官方文档 [Note: How to extend DeviceTypeTestBase](https://github.com/pytorch/pytorch/blob/main/torch/testing/_internal/common_device_type.py#L798)：

```python
# 在 Ascend/pytorch 中创建 NPU 测试基类

# 文件: torch_npu/testing/_internal/npu_test_base.py

from torch.testing._internal.common_device_type import DeviceTypeTestBase

class NPUTestBase(DeviceTypeTestBase):
    device_type = "npu"

    @classmethod
    def setUpClass(cls):
        # 初始化 NPU 环境
        pass

# 设置环境变量启用
# export TORCH_TEST_DEVICES=/path/to/npu_test_base.py
```

### 9.2 注册测试设备

```python
# 在 Ascend/pytorch 初始化时注册

import torch

# 注册 NPU 模块
torch._register_device_module('npu', torch_npu.npu)

# 设置 PrivateUse1 后端 (可选)
torch._C._set_privateuse1_backend_name("npu")
```