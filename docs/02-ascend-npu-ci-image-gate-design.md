# Ascend NPU CI 集成验证方案设计文档

## 项目定位与目标

### 1.1 项目背景

torch-npu 作为 PyTorch 的 NPU 设备扩展模块，存储在独立仓库 `Ascend/pytorch` 中，而非 PyTorch 主社区仓库。与 NVIDIA CUDA、AMD ROCm、Intel XPU 等设备不同，NPU 的适配代码不在 PyTorch 主仓，因此需要独立的 CI 机制来验证 torch-npu 与 PyTorch 的兼容性。

### 1.2 中间 CI 仓库定位

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     torch-npu ↔ pytorch 集成验证架构                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐         ┌──────────────────┐         ┌─────────────┐ │
│  │  Ascend/pytorch  │         │  pytorch-infra   │         │ pytorch/main │ │
│  │  (torch-npu)     │────────▶│  (中间CI仓库)     │◀────────│ (PyTorch官方) │ │
│  │                  │         │                  │         │             │ │
│  │  - NPU适配代码   │         │  - PR门禁触发    │         │ - nightly    │ │
│  │  - NPU算子实现   │         │  - 集成验证      │         │ - main分支   │ │
│  │  - NPU测试用例   │         │  - 结果追踪      │         │ - 设备测试   │ │
│  └──────────────────┘         └──────────────────┘         └─────────────┘ │
│                                                                             │
│  工作流程：                                                                  │
│  1. torch-npu PR 提交 → pytorch-infra 触发门禁                               │
│  2. pytorch-infra 拉取 PyTorch nightly                                      │
│  3. 构建 torch-npu + PyTorch nightly                                        │
│  4. 运行 NPU 测试（类似 CUDA/ROCm/XPU 在主仓的测试）                          │
│  5. 结果反馈到 torch-npu PR                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 核心目标

| 目标 | 说明 | 阶段 |
|------|------|------|
| **PR 集成验证** | torch-npu PR 自动触发与 PyTorch nightly 的集成测试 | 第一阶段 |
| **快速反馈** | 开发者提交后 30-60 分钟内获得测试结果 | 第一阶段 |
| **兼容性保障** | 及时发现 torch-npu 与 PyTorch API 的兼容问题 | 第一阶段 |
| **类主仓体验** | 提供类似 CUDA/ROCm 在 PyTorch 主仓的门禁体验 | 第一阶段 |
| **多架构测试** | 支持 910A/910B/310P 多种 NPU 架构 | 第二阶段 |
| **分布式测试** | HCCL 分布式训练验证 | 第二阶段 |
| **性能基准** | Inductor 性能回归检测 | 第三阶段 |

### 1.4 与其他设备的对比

| 设备 | 适配代码位置 | CI 触发方式 | 集成验证模式 |
|------|------------|------------|------------|
| **CUDA** | PyTorch 主仓 | PR + 定时 | 主仓直接测试 |
| **ROCm** | PyTorch 主仓 | PR + 定时 | 主仓直接测试 |
| **XPU** | PyTorch 主仓 | PR + 定时 | 主仓直接测试 |
| **NPU** | torch-npu 独立仓库 | 需要设计 | **中间 CI 仓库验证** |

NPU 的特殊之处在于代码不在主仓，因此需要通过中间 CI 仓库来实现类似主仓的集成验证体验。

---

## 二、镜像体系设计

### 2.1 镜像分层架构

CI 集成验证依赖稳定的镜像体系，确保每次测试环境一致、可复现。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         镜像分层架构                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: Base Image (基础层)                                                │
│  ─────────────────────────────────                                         │
│  作用: 提供操作系统和基础工具，作为所有镜像的起点                               │
│  内容:                                                                       │
│    - Ubuntu 22.04 LTS                                                       │
│    - Python 3.11 (官方构建)                                                  │
│    - 基础工具: git, curl, wget, build-essential                              │
│    - Docker 客户端                                                          │
│  更新频率: 每 6 个月或安全更新时                                               │
│  镜像示例: base-npu:ubuntu22.04-py311                                       │
│                                                                             │
│  Layer 2: CANN Image (驱动层)                                                │
│  ─────────────────────────────────                                         │
│  作用: 提供 NPU 驱动和 CANN 软件栈                                            │
│  内容:                                                                       │
│    - CANN Toolkit (对应版本)                                                 │
│    - NPU 驱动固件                                                           │
│    - HCCL (分布式通信库)                                                     │
│    - ATB (算子加速库)                                                        │
│  更新频率: CANN 版本发布时                                                    │
│  镜像示例: cann-npu:8.0.RC1                                                 │
│                                                                             │
│  Layer 3: CI Runner Image (运行层)                                           │
│  ─────────────────────────────────                                         │
│  作用: 提供 CI Runner 运行环境                                                │
│  内容:                                                                       │
│    - GitHub Actions Runner                                                  │
│    - 编译工具链: cmake, ninja, gcc                                           │
│    - 缓存工具: ccache                                                        │
│    - 测试工具: pytest, pytest-xdist                                         │
│  更新频率: Runner 版本更新或工具链变更时                                       │
│  镜像示例: runner-npu:cann8.0-runner2.311                                   │
│                                                                             │
│  Layer 4: Test Image (测试层)                                                │
│  ─────────────────────────────────                                         │
│  作用: 提供完整的测试运行环境                                                  │
│  内容:                                                                       │
│    - PyTorch nightly (特定版本)                                              │
│    - torch-npu (对应版本)                                                    │
│    - 测试依赖: numpy, expecttest, hypothesis                                │
│  更新频率: 每日构建                                                           │
│  镜像示例: test-npu:py2.7.0.dev20250330-cann8.0                              │
│                                                                             │
│  继承关系:                                                                   │
│  Base → CANN → CI Runner → Test                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 镜像构建策略

#### 2.2.1 构建触发机制

| 触发源 | 触发条件 | 构建目标 | 说明 |
|--------|---------|---------|------|
| **CANN 发布** | 新版本发布 | CANN Image → Runner Image | 华为发布新版 CANN 时自动触发 |
| **PyTorch nightly** | 每日更新 | Test Image | 每日 UTC 06:00 检查新版本 |
| **torch-npu 更新** | master 分支提交 | Test Image | torch-npu 有新提交时触发 |
| **手动触发** | workflow_dispatch | 所有层级 | 用于紧急修复或测试 |

#### 2.2.2 版本命名规范

```
镜像命名格式: [registry]/[namespace]/[name]:[tag]

Tag 组成规则:
├── Base Image: ubuntu22.04-py311-[date]
│   例: base-npu:ubuntu22.04-py311-20250301
│
├── CANN Image: [cann-version]-[npu-arch]
│   例: cann-npu:8.0.RC1-910B
│   例: cann-npu:8.1.beta-910A
│
├── Runner Image: [cann-version]-runner[runner-version]-[date]
│   例: runner-npu:cann8.0.RC1-runner2.311-20250315
│
└── Test Image: py[pytorch-ver]-cann[cann-ver]-[date]
│   例: test-npu:py2.7.0.dev20250330-cann8.0-20250330
│   例: test-npu:py2.6.0-cann7.0-20250301
│
特殊 Tag:
├── latest: 最新稳定版本
├── nightly: 每日构建版本（不稳定）
├── stable-[date]: 标记为稳定的版本
```

#### 2.2.3 镜像存储策略

| 存储位置 | 用途 | 优点 | 缺点 |
|---------|------|------|------|
| **华为云 SWR** | 主要生产镜像 | 国内访问快、NPU 生态集成 | 需要 IAM 配置 |
| **Docker Hub** | 公开镜像分发 | 全球可访问、免费公开仓库 | 国内访问慢、限流 |
| **GitHub Packages** | CI 内部镜像 | 与 GitHub Actions 集成 | 存储限制 |

推荐策略：
- **华为云 SWR** 作为主要生产镜像仓库
- 使用 `swr.cn-east-3.myhuaweicloud.com/ascend-ci/` 前缀
- 设置镜像保留策略：保留最近 30 天的每日镜像 + 所有稳定版本

### 2.3 CANN 版本兼容矩阵

CANN 是华为 NPU 软件栈的核心，其版本与 PyTorch、torch-npu 存在严格的兼容关系。

#### 2.3.1 官方兼容矩阵（参考华为文档）

| CANN 版本 | 支持的 NPU 架构 | Python 版本 | 发布日期 |
|-----------|----------------|------------|---------|
| **CANN 8.0.RC1** | 910A, 910B, 310P | 3.8-3.11 | 2024-12 |
| **CANN 7.0.1** | 910A, 910B, 310P | 3.8-3.10 | 2024-06 |
| **CANN 6.3.RC2** | 910A, 910B | 3.7-3.9 | 2023-12 |

#### 2.3.2 PyTorch + CANN + torch-npu 兼容矩阵

**关键兼容规则**：

1. **PyTorch → torch-npu**: torch-npu 需适配 PyTorch API，跟随 nightly 更新
2. **CANN → torch-npu**: torch-npu 底层算子依赖 CANN，版本必须匹配
3. **CANN → NPU 架构**: 不同架构可能需要不同 CANN 版本

| PyTorch 版本 | CANN 版本 | torch-npu 版本 | 验证状态 | 备注 |
|-------------|-----------|---------------|---------|------|
| **2.7.0.dev** | CANN 8.0.RC1 | v2.6.0+ | ✅ 稳定 | 当前推荐组合 |
| **2.6.0** | CANN 7.0.1 | v2.5.0 | ✅ 稳定 | LTS 版本 |
| **2.5.0** | CANN 6.3.RC2 | v2.4.0 | ⚠️ 维护中 | 仅安全更新 |
| **2.4.0** | CANN 6.3.RC2 | v2.3.0 | ❌ 已废弃 | 不建议使用 |

#### 2.3.3 兼容性验证策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     兼容性验证流程                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: 版本组合选择                                                        │
│  ─────────────────────────────                                             │
│  输入: PyTorch nightly commit + CANN 版本 + torch-npu commit                │
│  输出: 选择待验证的版本组合                                                   │
│                                                                             │
│  Step 2: 静态兼容检查                                                        │
│  ─────────────────────────────                                             │
│  检查项:                                                                     │
│    - CANN 版本号是否匹配 torch-npu 要求                                       │
│    - Python 版本是否在支持范围                                                │
│    - NPU 架构是否支持                                                         │
│  结果: 通过 → 继续构建；失败 → 标记不兼容                                      │
│                                                                             │
│  Step 3: 构建验证                                                            │
│  ─────────────────────────────                                             │
│  流程:                                                                       │
│    - 使用目标 CANN 镜像                                                       │
│    - 安装 PyTorch nightly                                                    │
│    - 构建 torch-npu wheel                                                   │
│    - 检查编译错误                                                             │
│  结果: 成功 → 继续；失败 → 创建兼容性 issue                                   │
│                                                                             │
│  Step 4: 运行时验证                                                          │
│  ─────────────────────────────                                             │
│  流程:                                                                       │
│    - 导入 torch_npu                                                          │
│    - NPU 设备初始化                                                          │
│    - 简单算子执行                                                            │
│  结果: 成功 → 更新兼容矩阵；失败 → 标记问题                                   │
│                                                                             │
│  Step 5: 更新兼容矩阵                                                        │
│  ─────────────────────────────                                             │
│  动作:                                                                       │
│    - 记录验证结果到 compatibility_matrix.json                                │
│    - 更新镜像 tag 标记                                                        │
│    - 发送通知（成功/失败）                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.3.4 兼容性矩阵数据结构

```json
// compatibility_matrix.json
{
  "version_matrix": [
    {
      "pytorch_version": "2.7.0.dev20250330",
      "pytorch_commit": "abc123def",
      "cann_version": "8.0.RC1",
      "torch_npu_version": "v2.6.0.20250330",
      "torch_npu_commit": "def456abc",
      "status": "verified",
      "verified_date": "2025-03-30",
      "test_results": {
        "smoke": "passed",
        "device_agnostic": "passed",
        "npu_specific": "passed"
      }
    }
  ],
  "metadata": {
    "last_updated": "2025-03-30T05:00:00Z",
    "source": "nightly-verification"
  }
}
```

### 2.4 镜像 Dockerfile 设计

#### 2.4.1 Base Image Dockerfile

```dockerfile
# dockerfiles/base-npu/Dockerfile
# Base Image: Ubuntu 22.04 + Python 3.11

FROM ubuntu:22.04

LABEL maintainer="CI Team"
LABEL description="Base image for NPU CI - Ubuntu 22.04 + Python 3.11"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装基础工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 3.11（从 deadsnakes PPA）
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get install -y python3.11 python3.11-dev python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 3.11 为默认
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# 安装 pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# 安装 ccache
RUN apt-get update && apt-get install -y ccache \
    && rm -rf /var/lib/apt/lists/*

# 配置 ccache
ENV CCACHE_DIR=/cache/ccache
ENV CCACHE_MAXSIZE=5G

# 创建工作目录
WORKDIR /workspace

# 创建缓存目录
RUN mkdir -p /cache/ccache /cache/pip

# 版本信息
RUN python --version && pip --version
```

#### 2.4.2 CANN Image Dockerfile

```dockerfile
# dockerfiles/cann-npu/Dockerfile
# CANN Image: 基于 Base Image，添加 CANN 软件栈

ARG BASE_IMAGE=base-npu:ubuntu22.04-py311-20250301
FROM ${BASE_IMAGE}

ARG CANN_VERSION=8.0.RC1
ARG NPU_ARCH=910B

LABEL maintainer="CI Team"
LABEL description="CANN image for NPU CI"
LABEL cann_version="${CANN_VERSION}"
LABEL npu_arch="${NPU_ARCH}"

# 设置环境变量
ENV CANN_VERSION=${CANN_VERSION}
ENV NPU_ARCH=${NPU_ARCH}
ENV ASCEND_HOME=/usr/local/Ascend
ENV ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit

# 安装 CANN Toolkit（从华为镜像源）
# 注意：实际安装需要 CANN 安装包，此处为示例
RUN mkdir -p ${ASCEND_HOME} \
    && cd /tmp \
    && wget -q https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/${CANN_VERSION}/Ascend-cann-toolkit_${CANN_VERSION}_linux-x86_64.run \
    && chmod +x Ascend-cann-toolkit*.run \
    && ./Ascend-cann-toolkit*.run --install --install-path=${ASCEND_HOME} \
    && rm -f Ascend-cann-toolkit*.run

# 安装 HCCL（分布式通信库）
RUN cd /tmp \
    && wget -q https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/${CANN_VERSION}/Ascend-cann-hccl_${CANN_VERSION}_linux-x86_64.run \
    && chmod +x Ascend-cann-hccl*.run \
    && ./Ascend-cann-hccl*.run --install --install-path=${ASCEND_HOME} \
    && rm -f Ascend-cann-hccl*.run

# 设置 CANN 环境变量
RUN echo "source ${ASCEND_HOME}/bin/setenv.bash" >> /etc/bash.bashrc

ENV PATH="${ASCEND_TOOLKIT_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${ASCEND_TOOLKIT_HOME}/lib64:${LD_LIBRARY_PATH}"
ENV PYTHONPATH="${ASCEND_TOOLKIT_HOME}/python/site-packages:${PYTHONPATH}"

# 验证 CANN 安装
RUN python -c "import te; print(f'CANN version: {te.__version__}')" || echo "CANN installed"

WORKDIR /workspace
```

#### 2.4.3 CI Runner Image Dockerfile

```dockerfile
# dockerfiles/runner-npu/Dockerfile
# CI Runner Image: 基于 CANN Image，添加 GitHub Actions Runner

ARG CANN_IMAGE=cann-npu:8.0.RC1-910B
FROM ${CANN_IMAGE}

ARG RUNNER_VERSION=2.311.0

LABEL maintainer="CI Team"
LABEL description="GitHub Actions Runner with NPU support"
LABEL runner_version="${RUNNER_VERSION}"

# 安装 Runner 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    libicu70 \
    && rm -rf /var/lib/apt/lists/*

# 创建 Runner 用户
RUN useradd -m -s /bin/bash runner \
    && mkdir -p /home/runner/work \
    && chown -R runner:runner /home/runner

# 下载并安装 GitHub Actions Runner
WORKDIR /home/runner
RUN curl -o actions-runner.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && tar xzf actions-runner.tar.gz \
    && rm actions-runner.tar.gz \
    && ./bin/installdependencies.sh \
    && chown -R runner:runner /home/runner

# 安装测试工具
RUN pip install --no-cache-dir \
    pytest \
    pytest-xdist \
    pytest-html \
    expecttest \
    hypothesis

# 配置缓存
ENV CCACHE_DIR=/cache/ccache
ENV PIP_CACHE_DIR=/cache/pip

# Runner 工作目录
WORKDIR /home/runner/work

# 切换到 runner 用户
USER runner

# Entrypoint（用于 Runner 注册和启动）
COPY entrypoint.sh /home/runner/entrypoint.sh
ENTRYPOINT ["/home/runner/entrypoint.sh"]
```

#### 2.4.4 Test Image Dockerfile

```dockerfile
# dockerfiles/test-npu/Dockerfile
# Test Image: 基于 Runner Image，添加 PyTorch 和 torch-npu

ARG RUNNER_IMAGE=runner-npu:cann8.0-runner2.311-20250315
FROM ${RUNNER_IMAGE}

ARG PYTORCH_VERSION=2.7.0.dev20250330
ARG TORCH_NPU_REPO=https://gitcode.com/Ascend/pytorch.git
ARG TORCH_NPU_BRANCH=master

LABEL maintainer="CI Team"
LABEL description="Test image with PyTorch nightly + torch-npu"
LABEL pytorch_version="${PYTORCH_VERSION}"

# 切换回 root 安装
USER root

# 安装 PyTorch nightly
RUN pip install --no-cache-dir --pre torch==${PYTORCH_VERSION} \
    --index-url https://download.pytorch.org/whl/nightly/cpu

# 克隆并构建 torch-npu
RUN cd /tmp \
    && git clone --depth=1 --branch=${TORCH_NPU_BRANCH} ${TORCH_NPU_REPO} torch-npu \
    && cd torch-npu \
    && python setup.py bdist_wheel \
    && pip install --no-cache-dir dist/torch_npu*.whl \
    && rm -rf /tmp/torch-npu

# 安装 PyTorch 测试依赖
RUN pip install --no-cache-dir \
    numpy \
    pyyaml \
    scipy \
    networkx \
    sympy

# 验证安装
RUN python -c "import torch; print(f'PyTorch: {torch.__version__}')"

# 切换回 runner 用户
USER runner

WORKDIR /home/runner/work
```

### 2.5 镜像仓库管理

#### 2.5.1 多仓库架构

采用三镜像仓库架构，兼顾全球分发、国内访问和企业生态集成：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         镜像仓库架构                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     构建源头：GitHub Actions                            │ │
│  │                                                                         │ │
│  │  镜像构建完成后，同步推送到三个仓库：                                       │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                              │
│  ──────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │
│  │  GitHub ghcr    │   │  Red Hat quay   │   │  华为云 SWR     │          │
│  │                 │   │                 │   │                 │          │
│  │  全球可访问     │   │  企业级稳定     │   │  国内极速访问   │          │
│  │  CI 集成友好    │   │  开源社区友好   │   │  NPU 生态集成   │          │
│  │  免费（公开）   │   │  免费（公开）   │   │  IAM 认证       │          │
│  │                 │   │                 │   │                 │          │
│  │  用途：         │   │  用途：         │   │  用途：         │          │
│  │  - CI Runner   │   │  - 公开分发     │   │  - 生产环境     │          │
│  │  - 开发测试    │   │  - 社区用户     │   │  - NPU Runner   │          │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘          │
│                                                                             │
│  仓库地址：                                                                  │
│  ─────────                                                                  │
│  ghcr.io/computing-infra/ascend-ci                                         │
│  quay.io/ascendpytorch/ascend-ci                                           │
│  swr.cn-east-3.myhuaweicloud.com/ascend-ci                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.5.2 仓库配置详情

```yaml
# 镜像仓库配置
registries:
  # GitHub Container Registry (ghcr)
  ghcr:
    name: "GitHub Container Registry"
    url: "ghcr.io"
    namespace: "computing-infra/ascend-ci"
    auth:
      type: "github_token"
      # 使用 GITHUB_TOKEN 或 PAT，自动集成 GitHub Actions
      # 公开镜像免费存储，私有镜像有存储限制
    features:
      - "与 GitHub Actions 无缝集成"
      - "支持 Package 安全扫描"
      - "全球 CDN 加速"
      - "公开镜像免费存储无限制"
    use_case:
      primary: "CI Runner 镜像"
      secondary: "开发测试环境"

  # Red Hat Quay.io
  quay:
    name: "Red Hat Quay"
    url: "quay.io"
    namespace: "ascendpytorch/ascend-ci"
    auth:
      type: "robot_account"
      # 创建 Robot Account 获取 token
      # quay.io/organization/ascendpytorch?tab=robots
    features:
      - "企业级镜像仓库"
      - "内置安全扫描（Clair）"
      - "镜像签名支持"
      - "开源社区广泛使用"
    use_case:
      primary: "公开镜像分发"
      secondary: "社区用户下载"

  # 华为云 SWR (Software Repository for Container)
  swr:
    name: "华为云 SWR"
    url: "swr.cn-east-3.myhuaweicloud.com"
    namespace: "ascend-ci"
    auth:
      type: "iam"
      region: "cn-east-3"
      # IAM 用户需要 SWR 推送权限
      # 或使用长期访问密钥 (AK/SK)
    features:
      - "国内访问速度最快"
      - "与华为云 CCE/CCI 集成"
      - "NPU 云原生支持"
      - "镜像同步功能"
    use_case:
      primary: "生产环境部署"
      secondary: "NPU Runner 运行"
```

#### 2.5.3 鉴权配置

**GitHub Actions 中配置 Secrets：**

```yaml
# GitHub Secrets 配置
secrets:
  # ghcr - 使用 GITHUB_TOKEN（自动提供）
  # 无需额外配置，公开仓库自动使用

  # quay.io - Robot Account Token
  QUAY_USERNAME: "ascendpytorch+robot_account_name"
  QUAY_PASSWORD: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

  # 华为云 SWR - IAM 或 AK/SK
  SWR_USERNAME: "cn-east-3@AKxxxxxxxxxxxx"
  SWR_PASSWORD: "SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Workflow 中的登录配置：**

```yaml
# 多仓库登录示例
steps:
  - name: Login to ghcr.io
    uses: docker/login-action@v3
    with:
      registry: ghcr.io
      username: ${{ github.actor }}
      password: ${{ secrets.GITHUB_TOKEN }}

  - name: Login to quay.io
    uses: docker/login-action@v3
    with:
      registry: quay.io
      username: ${{ secrets.QUAY_USERNAME }}
      password: ${{ secrets.QUAY_PASSWORD }}

  - name: Login to SWR
    uses: docker/login-action@v3
    with:
      registry: swr.cn-east-3.myhuaweicloud.com
      username: ${{ secrets.SWR_USERNAME }}
      password: ${{ secrets.SWR_PASSWORD }}
```

#### 2.5.4 镜像同步策略

```yaml
# 镜像同步策略
sync_policy:
  # 同步触发
  trigger:
    on_build_success: true  # 构建成功后立即同步
    on_stable_release: true # 稳定版本发布时同步

  # 同步顺序（构建后依次推送）
  order:
    - ghcr    # 优先推送（CI 使用）
    - swr     # 次优先（国内生产）
    - quay    # 最后推送（公开分发）

  # 同步范围
  scope:
    base_image:
      sync_to: ["ghcr", "swr"]  # Base Image 仅同步到 ghcr 和 swr
    cann_image:
      sync_to: ["swr"]          # CANN 镜像仅同步到 SWR（华为生态）
    runner_image:
      sync_to: ["ghcr", "swr"]  # Runner 镜像同步到 ghcr 和 swr
    test_image:
      sync_to: ["ghcr", "swr", "quay"]  # Test 镜像全量同步

  # 标签映射
  tag_mapping:
    ghcr:
      format: "[image-name]:[tag]"
      example: "ghcr.io/computing-infra/ascend-ci/test-npu:py2.7.0-cann8.0"
    quay:
      format: "[image-name]:[tag]"
      example: "quay.io/ascendpytorch/ascend-ci/test-npu:py2.7.0-cann8.0"
    swr:
      format: "[image-name]:[tag]"
      example: "swr.cn-east-3.myhuaweicloud.com/ascend-ci/test-npu:py2.7.0-cann8.0"
```

#### 2.5.5 镜像清理策略

```yaml
# 镜像清理策略（各仓库独立配置）
cleanup_policy:
  # ghcr 清理策略
  ghcr:
    retention:
      base_image: keep_all
      runner_image: keep_latest_10
      test_image: keep_days_30
    schedule: "0 4 * * *"  # UTC 04:00

  # quay 清理策略
  quay:
    retention:
      test_image: keep_days_60  # 公开分发保留更久
      stable_versions: keep_all
    schedule: "0 5 * * *"  # UTC 05:00
    # quay.io 支持通过 API 或 Web UI 配置自动清理

  # swr 清理策略
  swr:
    retention:
      base_image: keep_all
      cann_image: keep_versions: ["8.0.RC1", "7.0.1", "6.3.RC2"]
      runner_image: keep_days_90
      test_image: keep_days_30
    schedule: "0 3 * * *"  # UTC 03:00（北京时间 11:00）
    # 华为云 SWR 支持通过控制台或 API 配置生命周期规则

  # 通用保留规则
  common_rules:
    stable_tag_pattern: "stable-*"  # 稳定版本标签，全部保留
    latest_tag: always_keep          # latest 标签始终保留
    cann_version_tag: keep_supported # 支持的 CANN 版本镜像保留

---

## 三、镜像构建 Workflow

### 3.1 构建 Workflow 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    镜像构建 Workflow 架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ build-base-image.yml                                                   │ │
│  │                                                                         │ │
│  │   触发: 手动触发 / 定时(每6月)                                           │ │
│  │   输出: base-npu:ubuntu22.04-py311-[date]                              │ │
│  │   用途: 构建基础镜像                                                     │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ build-cann-image.yml                                                   │ │
│  │                                                                         │ │
│  │   触发: CANN 版本发布 / 手动触发                                         │ │
│  │   输入: CANN_VERSION, NPU_ARCH                                          │ │
│  │   输出: cann-npu:[version]-[arch]                                       │ │
│  │   用途: 构建 CANN 镜像                                                   │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ build-runner-image.yml                                                 │ │
│  │                                                                         │ │
│  │   触发: CANN 镜像更新 / Runner 版本更新 / 手动触发                        │ │
│  │   输入: CANN_IMAGE, RUNNER_VERSION                                      │ │
│  │   输出: runner-npu:cann[ver]-runner[ver]-[date]                         │ │
│  │   用途: 构建 CI Runner 镜像                                              │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ build-test-image.yml                                                   │ │
│  │                                                                         │ │
│  │   触发: 每日定时 / PyTorch nightly 更新 / torch-npu 更新                 │ │
│  │   输入: PYTORCH_VERSION, CANN_VERSION, TORCH_NPU_COMMIT                 │ │
│  │   输出: test-npu:py[ver]-cann[ver]-[date]                               │ │
│  │   用途: 构建测试镜像                                                     │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ verify-compatibility.yml                                               │ │
│  │                                                                         │ │
│  │   触发: 测试镜像构建完成后                                                │ │
│  │   输入: Test Image                                                      │ │
│  │   输出: 兼容性验证结果 + 更新兼容矩阵                                     │ │
│  │   用途: 验证版本组合兼容性                                                │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Base Image 构建 Workflow

```yaml
# .github/workflows/build-base-image.yml

name: build-base-image

on:
  workflow_dispatch:
    inputs:
      ubuntu_version:
        description: 'Ubuntu version'
        required: true
        default: '22.04'
      python_version:
        description: 'Python version'
        required: true
        default: '3.11'
  schedule:
    # 每 6 个月检查更新
    - cron: '0 0 1 */6 *'

env:
  REGISTRY: swr.cn-east-3.myhuaweicloud.com
  IMAGE_NAME: ascend-ci/base-npu

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to SWR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.SWR_USERNAME }}
          password: ${{ secrets.SWR_PASSWORD }}

      - name: Generate image metadata
        id: meta
        run: |
          DATE=$(date -u +"%Y%m%d")
          TAG="ubuntu${{ inputs.ubuntu_version }}-py${{ inputs.python_version }}-${DATE}"
          echo "tags=${TAG}" >> $GITHUB_OUTPUT
          echo "### Image Tag" >> $GITHUB_STEP_SUMMARY
          echo "${TAG}" >> $GITHUB_STEP_SUMMARY

      - name: Build and push Base Image
        uses: docker/build-push-action@v5
        with:
          context: ./dockerfiles/base-npu
          file: ./dockerfiles/base-npu/Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tags }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-to: type=inline
          build-args: |
            UBUNTU_VERSION=${{ inputs.ubuntu_version }}
            PYTHON_VERSION=${{ inputs.python_version }}

      - name: Verify image
        run: |
          docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tags }}
          docker run --rm ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tags }} \
            python --version
          docker run --rm ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tags }} \
            pip --version

      - name: Update image manifest
        run: |
          echo '{"base_image":{"tag":"${{ steps.meta.outputs.tags }}","date":"$(date -u)","ubuntu":"${{ inputs.ubuntu_version }}","python":"${{ inputs.python_version }}"}}' \
            >> image_manifest.json

      - name: Upload manifest
        uses: actions/upload-artifact@v4
        with:
          name: base-image-manifest
          path: image_manifest.json
```

### 3.3 CANN Image 构建 Workflow

```yaml
# .github/workflows/build-cann-image.yml

name: build-cann-image

on:
  workflow_dispatch:
    inputs:
      cann_version:
        description: 'CANN version (e.g., 8.0.RC1)'
        required: true
        default: '8.0.RC1'
      npu_arch:
        description: 'NPU architecture (910A, 910B, 310P)'
        required: true
        default: '910B'
      base_image:
        description: 'Base image tag'
        required: true
        default: 'ubuntu22.04-py311-20250301'
  repository_dispatch:
    types: [cann-release]

env:
  REGISTRY: swr.cn-east-3.myhuaweicloud.com
  IMAGE_NAME: ascend-ci/cann-npu

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tag }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to SWR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.SWR_USERNAME }}
          password: ${{ secrets.SWR_PASSWORD }}

      - name: Validate CANN version
        id: validate
        run: |
          # 检查 CANN 版本格式
          VERSION="${{ inputs.cann_version }}"
          if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.(RC[0-9]+|[0-9]+)$ ]]; then
            echo "::error::Invalid CANN version format: $VERSION"
            exit 1
          fi
          echo "valid=true" >> $GITHUB_OUTPUT

      - name: Download CANN packages
        run: |
          mkdir -p ./dockerfiles/cann-npu/packages
          CANN_VER="${{ inputs.cann_version }}"

          # 下载 CANN Toolkit
          wget -q \
            "https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/${CANN_VER}/Ascend-cann-toolkit_${CANN_VER}_linux-x86_64.run" \
            -O ./dockerfiles/cann-npu/packages/Ascend-cann-toolkit.run

          # 下载 HCCL
          wget -q \
            "https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/${CANN_VER}/Ascend-cann-hccl_${CANN_VER}_linux-x86_64.run" \
            -O ./dockerfiles/cann-npu/packages/Ascend-cann-hccl.run

          # 验证下载
          ls -la ./dockerfiles/cann-npu/packages/

      - name: Generate image tag
        id: meta
        run: |
          TAG="${{ inputs.cann_version }}-${{ inputs.npu_arch }}"
          echo "tag=${TAG}" >> $GITHUB_OUTPUT
          echo "### Image Tag: ${TAG}" >> $GITHUB_STEP_SUMMARY

      - name: Build and push CANN Image
        uses: docker/build-push-action@v5
        with:
          context: ./dockerfiles/cann-npu
          file: ./dockerfiles/cann-npu/Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tag }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:cann${{ inputs.cann_version }}
          build-args: |
            BASE_IMAGE=ascend-ci/base-npu:${{ inputs.base_image }}
            CANN_VERSION=${{ inputs.cann_version }}
            NPU_ARCH=${{ inputs.npu_arch }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:cann${{ inputs.cann_version }}

      - name: Verify CANN installation
        run: |
          docker run --rm ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tag }} \
            python -c "import te; print(f'CANN version: {te.__version__}')" || \
            echo "CANN package installed (runtime verification requires NPU hardware)"

      - name: Trigger runner image build
        if: success()
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.WORKFLOW_TOKEN }}
          script: |
            github.rest.repos.createDispatchEvent({
              owner: context.repo.owner,
              repo: context.repo.repo,
              event_type: 'cann-image-built',
              client_payload: {
                cann_image: '${{ steps.meta.outputs.tag }}',
                cann_version: '${{ inputs.cann_version }}',
                npu_arch: '${{ inputs.npu_arch }}'
              }
            });

      - name: Update compatibility matrix
        run: |
          cat > cann_version.json << EOF
          {
            "cann_version": "${{ inputs.cann_version }}",
            "npu_arch": "${{ inputs.npu_arch }}",
            "image_tag": "${{ steps.meta.outputs.tag }}",
            "build_date": "$(date -u)",
            "status": "available"
          }
          EOF

      - name: Upload version info
        uses: actions/upload-artifact@v4
        with:
          name: cann-version-info
          path: cann_version.json
```

### 3.4 Runner Image 构建 Workflow

```yaml
# .github/workflows/build-runner-image.yml

name: build-runner-image

on:
  workflow_dispatch:
    inputs:
      cann_image:
        description: 'CANN image tag (e.g., 8.0.RC1-910B)'
        required: true
      runner_version:
        description: 'GitHub Actions Runner version'
        required: true
        default: '2.311.0'
  repository_dispatch:
    types: [cann-image-built]
  schedule:
    # Runner 版本更新检查（每周）
    - cron: '0 6 * * 1'

env:
  REGISTRY: swr.cn-east-3.myhuaweicloud.com
  IMAGE_NAME: ascend-ci/runner-npu

jobs:
  check-runner-version:
    runs-on: ubuntu-latest
    outputs:
      latest_runner: ${{ steps.check.outputs.version }}

    steps:
      - name: Check latest Runner version
        id: check
        run: |
          LATEST=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')
          echo "version=${LATEST}" >> $GITHUB_OUTPUT
          echo "Latest Runner version: ${LATEST}"

  build:
    needs: check-runner-version
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tag }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Determine inputs
        id: inputs
        run: |
          # 处理触发来源
          if [[ "${{ github.event_name }}" == "repository_dispatch" ]]; then
            CANN_IMAGE="${{ github.event.client_payload.cann_image }}"
            CANN_VER="${{ github.event.client_payload.cann_version }}"
          else
            CANN_IMAGE="${{ inputs.cann_image }}"
            CANN_VER=$(echo "${{ inputs.cann_image }}" | cut -d'-' -f1)
          fi

          RUNNER_VER="${{ inputs.runner_version || needs.check-runner-version.outputs.latest_runner }}"

          echo "cann_image=${CANN_IMAGE}" >> $GITHUB_OUTPUT
          echo "cann_version=${CANN_VER}" >> $GITHUB_OUTPUT
          echo "runner_version=${RUNNER_VER}" >> $GITHUB_OUTPUT

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to SWR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.SWR_USERNAME }}
          password: ${{ secrets.SWR_PASSWORD }}

      - name: Generate image tag
        id: meta
        run: |
          DATE=$(date -u +"%Y%m%d")
          CANN_VER="${{ steps.inputs.outputs.cann_version }}"
          RUNNER_VER="${{ steps.inputs.outputs.runner_version }}"
          TAG="cann${CANN_VER}-runner${RUNNER_VER}-${DATE}"
          echo "tag=${TAG}" >> $GITHUB_OUTPUT
          echo "### Image Tag: ${TAG}" >> $GITHUB_STEP_SUMMARY

      - name: Build and push Runner Image
        uses: docker/build-push-action@v5
        with:
          context: ./dockerfiles/runner-npu
          file: ./dockerfiles/runner-npu/Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tag }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:cann${{ steps.inputs.outputs.cann_version }}-latest
          build-args: |
            CANN_IMAGE=ascend-ci/cann-npu:${{ steps.inputs.outputs.cann_image }}
            RUNNER_VERSION=${{ steps.inputs.outputs.runner_version }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:cann${{ steps.inputs.outputs.cann_version }}-latest

      - name: Prepare Runner entrypoint script
        run: |
          cat > ./dockerfiles/runner-npu/entrypoint.sh << 'EOF'
          #!/bin/bash
          set -e

          # 设置 NPU 设备权限
          if [[ -e /dev/davinci0 ]]; then
            sudo chmod 666 /dev/davinci* 2>/dev/null || true
            sudo chmod 666 /dev/davinci_manager 2>/dev/null || true
          fi

          # 设置 CANN 环境
          source /usr/local/Ascend/bin/setenv.bash 2>/dev/null || true

          # Runner 注册逻辑
          if [[ -n "$RUNNER_TOKEN" ]]; then
            ./config.sh --url "$RUNNER_REPO" --token "$RUNNER_TOKEN" --labels "$RUNNER_LABELS"
          fi

          # 启动 Runner
          ./run.sh
          EOF
          chmod +x ./dockerfiles/runner-npu/entrypoint.sh

      - name: Update runner manifest
        run: |
          cat > runner_manifest.json << EOF
          {
            "cann_version": "${{ steps.inputs.outputs.cann_version }}",
            "runner_version": "${{ steps.inputs.outputs.runner_version }}",
            "image_tag": "${{ steps.meta.outputs.tag }}",
            "build_date": "$(date -u)",
            "capabilities": ["npu", "build", "test"]
          }
          EOF

      - name: Upload manifest
        uses: actions/upload-artifact@v4
        with:
          name: runner-image-manifest
          path: runner_manifest.json
```

### 3.5 Test Image 构建 Workflow

```yaml
# .github/workflows/build-test-image.yml

name: build-test-image

on:
  workflow_dispatch:
    inputs:
      pytorch_version:
        description: 'PyTorch nightly version (e.g., 2.7.0.dev20250330)'
        required: true
      cann_version:
        description: 'CANN version'
        required: true
        default: '8.0.RC1'
      torch_npu_commit:
        description: 'torch-npu commit SHA (optional, use latest if empty)'
        required: false
  schedule:
    # 每日构建（UTC 06:00 = 北京时间 14:00）
    - cron: '0 6 * * *'
  repository_dispatch:
    types: [torch-npu-update]

env:
  REGISTRY: swr.cn-east-3.myhuaweicloud.com
  IMAGE_NAME: ascend-ci/test-npu

jobs:
  get-versions:
    runs-on: ubuntu-latest
    outputs:
      pytorch_version: ${{ steps.pytorch.outputs.version }}
      pytorch_commit: ${{ steps.pytorch.outputs.commit }}
      torch_npu_commit: ${{ steps.torch_npu.outputs.commit }}
      cann_version: ${{ steps.cann.outputs.version }}

    steps:
      - name: Get PyTorch nightly version
        id: pytorch
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            PY_VER="${{ inputs.pytorch_version }}"
          else
            # 获取最新 nightly 版本
            PY_VER=$(pip index versions torch --pre --index-url https://download.pytorch.org/whl/nightly/cpu 2>/dev/null \
              | grep -oP '2\.\d+\.\d+\.dev\d+' | head -1)
          fi

          # 获取对应的 commit
          PY_COMMIT=$(curl -s "https://download.pytorch.org/whl/nightly/cpu/torch-${PY_VER}.whl" 2>/dev/null \
            | strings | grep -oP '[a-f0-9]{12}' | head -1 || echo "unknown")

          echo "version=${PY_VER}" >> $GITHUB_OUTPUT
          echo "commit=${PY_COMMIT}" >> $GITHUB_OUTPUT
          echo "PyTorch: ${PY_VER}"

      - name: Get torch-npu latest commit
        id: torch_npu
        run: |
          if [[ "${{ inputs.torch_npu_commit }}" != "" ]]; then
            NPU_COMMIT="${{ inputs.torch_npu_commit }}"
          else
            NPU_COMMIT=$(curl -s "https://gitcode.com/api/v5/repos/Ascend/pytorch/commits/master" \
              | jq -r '.sha' | cut -c1-12)
          fi
          echo "commit=${NPU_COMMIT}" >> $GITHUB_OUTPUT
          echo "torch-npu commit: ${NPU_COMMIT}"

      - name: Determine CANN version
        id: cann
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            CANN_VER="${{ inputs.cann_version }}"
          else
            # 从兼容矩阵获取推荐的 CANN 版本
            CANN_VER="8.0.RC1"  # 默认使用稳定版本
          fi
          echo "version=${CANN_VER}" >> $GITHUB_OUTPUT

  build:
    needs: get-versions
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tag }}
      build_status: ${{ steps.build.outputs.status }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to SWR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.SWR_USERNAME }}
          password: ${{ secrets.SWR_PASSWORD }}

      - name: Check compatibility matrix
        id: compatibility
        run: |
          PY_VER="${{ needs.get-versions.outputs.pytorch_version }}"
          CANN_VER="${{ needs.get-versions.outputs.cann_version }}"

          # 验证版本组合是否已知兼容
          # 这里可以调用兼容性检查 API 或读取兼容矩阵文件
          echo "compatible=true" >> $GITHUB_OUTPUT
          echo "Checking compatibility: PyTorch ${PY_VER} + CANN ${CANN_VER}"

      - name: Generate image tag
        id: meta
        run: |
          DATE=$(date -u +"%Y%m%d")
          PY_VER="${{ needs.get-versions.outputs.pytorch_version }}"
          CANN_VER="${{ needs.get-versions.outputs.cann_version }}"

          # 简化版本号用于 tag
          PY_TAG=$(echo "${PY_VER}" | sed 's/\.dev/-dev/')
          TAG="py${PY_TAG}-cann${CANN_VER}-${DATE}"

          echo "tag=${TAG}" >> $GITHUB_OUTPUT
          echo "### Test Image Tag: ${TAG}" >> $GITHUB_STEP_SUMMARY

      - name: Build Test Image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: ./dockerfiles/test-npu
          file: ./dockerfiles/test-npu/Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tag }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:nightly
          build-args: |
            RUNNER_IMAGE=ascend-ci/runner-npu:cann${{ needs.get-versions.outputs.cann_version }}-latest
            PYTORCH_VERSION=${{ needs.get-versions.outputs.pytorch_version }}
            TORCH_NPU_COMMIT=${{ needs.get-versions.outputs.torch_npu_commit }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:nightly
          cache-to: type=inline

      - name: Verify build success
        if: success()
        run: |
          echo "status=success" >> $GITHUB_OUTPUT

      - name: Trigger compatibility verification
        if: success()
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.WORKFLOW_TOKEN }}
          script: |
            github.rest.repos.createDispatchEvent({
              owner: context.repo.owner,
              repo: context.repo.repo,
              event_type: 'test-image-built',
              client_payload: {
                test_image: '${{ steps.meta.outputs.tag }}',
                pytorch_version: '${{ needs.get-versions.outputs.pytorch_version }}',
                pytorch_commit: '${{ needs.get-versions.outputs.pytorch_commit }}',
                cann_version: '${{ needs.get-versions.outputs.cann_version }}',
                torch_npu_commit: '${{ needs.get-versions.outputs.torch_npu_commit }}'
              }
            });

      - name: Upload build info
        uses: actions/upload-artifact@v4
        with:
          name: test-image-info
          path: |
            test_image_info.json
```

### 3.6 兼容性验证 Workflow

```yaml
# .github/workflows/verify-compatibility.yml

name: verify-compatibility

on:
  repository_dispatch:
    types: [test-image-built]
  workflow_dispatch:
    inputs:
      test_image:
        description: 'Test image tag to verify'
        required: true

jobs:
  verify:
    runs-on: [self-hosted, npu-910b]
    timeout-minutes: 30
    outputs:
      status: ${{ steps.verify.outputs.status }}

    steps:
      - name: Get version info
        id: versions
        run: |
          if [[ "${{ github.event_name }}" == "repository_dispatch" ]]; then
            echo "pytorch_version=${{ github.event.client_payload.pytorch_version }}" >> $GITHUB_OUTPUT
            echo "cann_version=${{ github.event.client_payload.cann_version }}" >> $GITHUB_OUTPUT
            echo "torch_npu_commit=${{ github.event.client_payload.torch_npu_commit }}" >> $GITHUB_OUTPUT
            echo "test_image=${{ github.event.client_payload.test_image }}" >> $GITHUB_OUTPUT
          else
            echo "test_image=${{ inputs.test_image }}" >> $GITHUB_OUTPUT
          fi

      - name: Pull Test Image
        run: |
          docker pull swr.cn-east-3.myhuaweicloud.com/ascend-ci/test-npu:${{ steps.versions.outputs.test_image }}

      - name: Setup NPU environment
        run: |
          npu-smi info
          sudo chmod 666 /dev/davinci* 2>/dev/null || true
          sudo chmod 666 /dev/davinci_manager 2>/dev/null || true

      - name: Run Smoke Tests in container
        id: verify
        run: |
          docker run --rm \
            --device=/dev/davinci0 \
            --device=/dev/davinci_manager \
            -e PYTORCH_TESTING_DEVICE_ONLY_FOR=npu \
            swr.cn-east-3.myhuaweicloud.com/ascend-ci/test-npu:${{ steps.versions.outputs.test_image }} \
            python -c "
import torch
import torch_npu

print(f'PyTorch: {torch.__version__}')
print(f'torch_npu available: {torch.npu.is_available()}')
print(f'NPU count: {torch.npu.device_count()}')

# 基本张量操作
x = torch.randn(2, 3).to('npu')
y = x + x
print(f'Tensor ops: OK')

# 简单模型
model = torch.nn.Linear(3, 2).to('npu')
out = model(x)
print(f'Model forward: OK')
"

          if [[ $? -eq 0 ]]; then
            echo "status=verified" >> $GITHUB_OUTPUT
          else
            echo "status=failed" >> $GITHUB_OUTPUT
          fi

      - name: Update compatibility matrix
        if: always()
        run: |
          STATUS="${{ steps.verify.outputs.status }}"
          DATE=$(date -u +"%Y-%m-%d")

          cat > compatibility_entry.json << EOF
          {
            "pytorch_version": "${{ steps.versions.outputs.pytorch_version }}",
            "cann_version": "${{ steps.versions.outputs.cann_version }}",
            "torch_npu_commit": "${{ steps.versions.outputs.torch_npu_commit }}",
            "test_image": "${{ steps.versions.outputs.test_image }}",
            "status": "${STATUS}",
            "verified_date": "${DATE}"
          }
          EOF

          # 更新兼容矩阵文件（实际需要追加到现有文件）
          echo "Compatibility entry created"

      - name: Upload compatibility entry
        uses: actions/upload-artifact@v4
        with:
          name: compatibility-entry-${{ steps.versions.outputs.test_image }}
          path: compatibility_entry.json

      - name: Notify on failure
        if: failure()
        run: |
          echo "::warning::Compatibility verification failed for ${{ steps.versions.outputs.test_image }}"
          # 实际应发送通知（邮件、Slack 等）

  update-matrix:
    needs: verify
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Download compatibility entry
        uses: actions/download-artifact@v4
        with:
          pattern: compatibility-entry-*

      - name: Update compatibility_matrix.json
        run: |
          # 读取现有兼容矩阵
          if [[ -f "compatibility_matrix.json" ]]; then
            MATRIX=$(cat compatibility_matrix.json)
          else
            MATRIX='{"version_matrix": [], "metadata": {}}'
          fi

          # 合合新条目
          NEW_ENTRY=$(cat compatibility_entry*/compatibility_entry.json)
          jq ".version_matrix += [${NEW_ENTRY}]" <<< "${MATRIX}" > compatibility_matrix_new.json

          # 更新元数据
          jq ".metadata.last_updated = \"$(date -u)\"" compatibility_matrix_new.json > compatibility_matrix.json

      - name: Commit compatibility matrix update
        run: |
          git config user.name "CI Bot"
          git config user.email "ci-bot@example.com"
          git add compatibility_matrix.json
          git commit -m "Update compatibility matrix: ${{ needs.verify.outputs.status }}"
          git push
```

### 3.7 镜像清理 Workflow

```yaml
# .github/workflows/cleanup-images.yml

name: cleanup-images

on:
  schedule:
    # 每日凌晨 3 点执行清理
    - cron: '0 3 * * *'
  workflow_dispatch:

jobs:
  cleanup:
    runs-on: ubuntu-latest

    steps:
      - name: Login to SWR
        uses: docker/login-action@v3
        with:
          registry: swr.cn-east-3.myhuaweicloud.com
          username: ${{ secrets.SWR_USERNAME }}
          password: ${{ secrets.SWR_PASSWORD }}

      - name: Get image list
        id: images
        run: |
          # 获取所有镜像 tag
          docker images --format "{{.Repository}}:{{.Tag}}" | grep "ascend-ci/" > image_list.txt
          echo "Found images:"
          cat image_list.txt

      - name: Apply retention policy
        run: |
          DATE=$(date -u +"%Y%m%d")
          RETENTION_DAYS=30
          CUTOFF_DATE=$(date -u -d "-${RETENTION_DAYS} days" +"%Y%m%d")

          echo "Cutoff date: ${CUTOFF_DATE}"
          echo "Removing test images older than ${RETENTION_DAYS} days..."

          # 模拟清理（实际需要调用 SWR API）
          while read -r image; do
            TAG=$(echo "$image" | cut -d':' -f2)
            IMG_DATE=$(echo "$TAG" | grep -oP '\d{8}' | tail -1)

            if [[ -n "$IMG_DATE" && "$IMG_DATE" < "$CUTOFF_DATE" ]]; then
              # 检查是否是稳定版本（不删除）
              if [[ ! "$TAG" =~ "stable" ]]; then
                echo "Would delete: $image"
                # docker rmi "$image"  # 实际删除命令
              fi
            fi
          done < image_list.txt

      - name: Report cleanup summary
        run: |
          echo "### Cleanup Summary" >> $GITHUB_STEP_SUMMARY
          echo "Retention policy: ${RETENTION_DAYS} days" >> $GITHUB_STEP_SUMMARY
          echo "Images checked: $(wc -l < image_list.txt)" >> $GITHUB_STEP_SUMMARY
```

### 3.8 Workflow 触发关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Workflow 触发关系                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  外部触发源:                                                                  │
│  ───────────                                                                │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │ CANN 版本发布   │     │ PyTorch nightly │     │ torch-npu 提交  │       │
│  │ (华为官方)      │     │ (每日更新)      │     │ (GitCode)       │       │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│         │                        │                        │                 │
│         │ repository_dispatch    │ schedule               │ dispatch        │
│         ↓                        ↓                        ↓                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ build-cann-image.yml                                                   │ │
│  │         │                                                              │ │
│  │         │ cann-image-built (dispatch)                                  │ │
│  │         ↓                                                              │ │
│  │ ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │ │ build-runner-image.yml                                             │ │ │
│  │ │         │                                                          │ │ │
│  │ │         │ runner-image-built (隐式，通过 tag 更新)                  │ │ │
│  │ │         ↓                                                          │ │ │
│  │ │ ┌───────────────────────────────────────────────────────────────┐ │ │ │
│  │ │ │ build-test-image.yml                                           │ │ │ │
│  │ │ │         │                                                      │ │ │ │
│  │ │ │         │ test-image-built (dispatch)                          │ │ │ │
│  │ │ │         ↓                                                      │ │ │ │
│  │ │ │ ┌───────────────────────────────────────────────────────────┐ │ │ │ │
│  │ │ │ │ verify-compatibility.yml                                   │ │ │ │ │
│  │ │ │ │         │                                                  │ │ │ │ │
│  │ │ │ │         │ 更新兼容矩阵                                      │ │ │ │ │
│  │ │ │ │         ↓                                                  │ │ │ │ │
│  │ │ │ │ ┌─────────────────────────────────────────────────────────┐│ │ │ │ │
│  │ │ │ │ │ compatibility_matrix.json                                ││ │ │ │ │
│  │ │ │ │ └─────────────────────────────────────────────────────────┘│ │ │ │ │
│  │ │ │ └───────────────────────────────────────────────────────────┘ │ │ │ │
│  │ │ └───────────────────────────────────────────────────────────────┘ │ │ │
│  │ └───────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  定时清理:                                                                   │
│  ───────────                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ cleanup-images.yml (每日 03:00 UTC)                                    │ │
│  │   - 删除过期镜像                                                        │ │
│  │   - 更新镜像清单                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、第一阶段方案设计：PR 集成验证

### 4.1 设计目标

第一阶段的核心目标：让 torch-npu 的 PR 或最新代码能够及时与 PyTorch 集成测试，类似 NV/AMD 设备在 PyTorch 主仓的基础测试体验。

**关键指标**：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 触发延迟 | < 1 分钟 | PR 提交后立即触发 |
| Smoke 测试 | < 15 分钟 | 快速验证基本功能 |
| 完整测试 | < 60 分钟 | 设备无关测试 + NPU 特定测试 |
| 反馈方式 | PR Comment | 结果直接反馈到 PR |

### 4.2 torch-npu 与 PyTorch 集成机制

#### 4.2.1 PrivateUse1 Backend

torch-npu 使用 PyTorch 的 `PrivateUse1` 机制注册 NPU 设备，这是实现设备扩展的核心机制：

```python
# torch_npu/__init__.py

import torch
import torch_npu

# 1. 重命名 PrivateUse1 后端为 "npu"
torch.utils.rename_privateuse1_backend("npu")

# 2. 注册 NPU 模块到 PyTorch
torch._register_device_module('npu', torch_npu.npu)

# 3. 生成设备相关方法（类似 torch.cuda）
torch.utils.generate_methods_for_privateuse1_backend(
    for_tensor=True,       # tensor.to('npu'), tensor.npu()
    for_module=True,       # module.to('npu')
    for_storage=True,      # storage.npu()
    unsupported_dtype=[]
)

# 结果：torch.npu 可用，API 与 torch.cuda 对齐
# - torch.npu.is_available()
# - torch.npu.current_device()
# - torch.npu.device_count()
# - tensor.to('npu') / tensor.npu()
```

#### 4.2.2 设备无关测试框架

PyTorch 提供了 `instantiate_device_type_tests` 机制，允许同一测试模板为不同设备实例化测试：

```python
# torch/testing/_internal/common_device_type.py

class NPUTestBase(DeviceTypeTestBase):
    device_type = "npu"

    @classmethod
    def setUpClass(cls):
        if not torch.npu.is_available():
            raise unittest.SkipTest("NPU not available")
        cls.primary_device = f"npu:{torch.npu.current_device()}"
        cls.device_mod = torch.npu

# 通过环境变量启用 NPU 测试
# export PYTORCH_TESTING_DEVICE_ONLY_FOR="npu"
```

#### 4.2.3 环境变量控制

| 环境变量 | 说明 | 用法 |
|---------|------|------|
| `PYTORCH_TESTING_DEVICE_ONLY_FOR` | 仅运行指定设备测试 | `npu` 或 `npu,cpu` |
| `PYTORCH_TESTING_DEVICE_EXCEPT_FOR` | 排除指定设备测试 | `cuda,xpu` |
| `TORCH_TEST_DEVICES` | 自定义测试设备路径 | `/path/to/npu_test_base.py` |

### 4.3 集成验证流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    torch-npu PR 集成验证流程                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: PR 触发                                                             │
│  ─────────────────                                                          │
│  torch-npu PR 提交 → GitHub Webhook → pytorch-infra workflow 触发            │
│                                                                             │
│  Step 2: PyTorch Nightly 获取                                                │
│  ───────────────────────                                                    │
│  pip install --pre torch --index-url https://download.pytorch.org/whl/nightly│
│  记录版本信息：PyTorch version + commit SHA                                  │
│                                                                             │
│  Step 3: torch-npu 构建                                                      │
│  ───────────────────                                                        │
│  python setup.py bdist_wheel → 安装 torch_npu wheel                          │
│                                                                             │
│  Step 4: 测试执行                                                            │
│  ─────────────                                                              │
│  Layer 1: Smoke Tests (2-5 min)                                             │
│    - torch_npu 导入验证                                                     │
│    - NPU 设备检测                                                           │
│    - 基本张量操作                                                           │
│                                                                             │
│  Layer 2: Device-Agnostic Tests (15-30 min)                                 │
│    - PyTorch 通用测试的 NPU 子集                                             │
│    - test_torch.py, test_ops.py, test_nn.py                                 │
│    - 分片执行                                                               │
│                                                                             │
│  Layer 3: NPU-Specific Tests (30-60 min)                                    │
│    - torch-npu 专用测试                                                     │
│    - NPU 算子、图模式等                                                     │
│                                                                             │
│  Step 5: 结果反馈                                                            │
│  ─────────────                                                              │
│  - PR Comment: 测试摘要                                                     │
│  - GitHub Check: 通过/失败状态                                              │
│  - Issue: 失败时自动创建兼容性问题                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 测试分层策略

#### 4.4.1 分层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          测试分层策略                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 1: Smoke Tests (2-5 分钟)                                      │   │
│  │ ─────────────────────────────────────────────────────────────────── │   │
│  │ 目的: 快速验证基本功能，发现严重集成问题                                 │   │
│  │ 触发: 每个 PR 必须                                                    │   │
│  │ 阻塞: 必须通过才能继续下一层                                            │   │
│  │ 内容:                                                                │   │
│  │   - torch_npu 导入测试                                               │   │
│  │   - NPU 设备检测和初始化                                              │   │
│  │   - 简单张量创建和运算                                                │   │
│  │   - PrivateUse1 后端注册验证                                          │   │
│  │   - 与 torch.cuda API 对齐检查                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 2: Device-Agnostic Tests (15-30 分钟)                          │   │
│  │ ─────────────────────────────────────────────────────────────────── │   │
│  │ 目的: 验证 PyTorch 通用功能在 NPU 上的正确性                           │   │
│  │ 触发: Smoke 通过后                                                   │   │
│  │ 阻塞: 建议通过才能合入 PR                                              │   │
│  │ 内容:                                                                │   │
│  │   - test_torch.py (核心张量操作)                                     │   │
│  │   - test_ops.py (算子测试)                                           │   │
│  │   - test_nn.py (神经网络模块)                                        │   │
│  │   - test_autograd.py (自动微分)                                      │   │
│  │ 方式: 6 分片并行执行                                                  │   │
│  │ 环境: PYTORCH_TESTING_DEVICE_ONLY_FOR=npu                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 3: NPU-Specific Tests (30-60 分钟)                             │   │
│  │ ─────────────────────────────────────────────────────────────────── │   │
│  │ 目的: 验证 torch-npu 专用功能                                        │   │
│  │ 触发: Device-Agnostic 通过后                                         │   │
│  │ 阻塞: 必须通过                                                       │   │
│  │ 内容:                                                                │   │
│  │   - test/test_npu.py (NPU 核心功能)                                  │   │
│  │   - test/test_custom_op.py (自定义算子)                              │   │
│  │   - test/test_aclnn.py (ACL NN 算子)                                 │   │
│  │ 方式: pytest -n auto 并行执行                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 4: Extended Tests (异步执行，不阻塞 PR)                         │   │
│  │ ─────────────────────────────────────────────────────────────────── │   │
│  │ 目的: 深度验证复杂场景                                                │   │
│  │ 触发: PR 合入后或每日定时                                             │   │
│  │ 阻塞: 不阻塞 PR 合入                                                  │   │
│  │ 内容:                                                                │   │
│  │   - distributed/test_c10d* (分布式训练)                              │   │
│  │   - test/test_hccl.py (HCCL 通信)                                    │   │
│  │   - inductor/test_torchinductor.py (Inductor 编译)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.4.2 参考其他设备在 PyTorch 主仓的测试模式

| 设备 | Smoke 测试 | Default 测试 | 分布式测试 | 触发方式 |
|------|-----------|-------------|-----------|---------|
| **CUDA** | test_cuda_smoke | trunk.yml 分片 | distributed | 每次 PR |
| **ROCm** | test_transformers (smoke) | rocm-mi300.yml 6分片 | rocm-distributed | 定时 + tag |
| **XPU** | smoke_xpu | xpu.yml 6-12分片 | - | 定时 + tag |
| **NPU (设计)** | smoke_test.py | 6分片 | Layer 4 | PR 触发 |

#### 4.4.3 Smoke Test 设计

```python
# test/smoke_test.py

"""
torch-npu Smoke 测试
目的：快速验证 torch-npu 与 PyTorch nightly 的基本集成
运行时间：2-5 分钟
"""

import sys
import torch

def test_pytorch_import():
    """验证 PyTorch 版本"""
    print(f"PyTorch version: {torch.__version__}")
    print(f"PyTorch commit: {torch.__git_version__}")
    assert torch.__version__.startswith("2."), "PyTorch version check failed"
    print("✓ PyTorch import successful")

def test_torch_npu_import():
    """验证 torch_npu 导入"""
    try:
        import torch_npu
        print(f"torch_npu version: {torch_npu.__version__}")
        print("✓ torch_npu import successful")
    except ImportError as e:
        print(f"✗ torch_npu import failed: {e}")
        raise

def test_npu_device():
    """验证 NPU 设备可用"""
    import torch_npu

    assert torch.npu.is_available(), "NPU not available"
    device_count = torch.npu.device_count()
    print(f"✓ NPU available, count: {device_count}")

    if device_count > 0:
        device = torch.npu.current_device()
        device_name = torch.npu.get_device_name(device)
        print(f"  Device: {device}, Name: {device_name}")

def test_tensor_operations():
    """验证基本张量操作"""
    # CPU 张量
    x = torch.randn(2, 3)
    print(f"✓ Tensor creation on CPU: shape={x.shape}")

    # 移动到 NPU
    x_npu = x.to('npu')
    assert x_npu.device.type == 'npu'
    print(f"✓ Tensor moved to NPU")

    # NPU 运算
    y_npu = x_npu + x_npu
    z_npu = torch.matmul(x_npu, x_npu.T)
    print(f"✓ Basic operations: add, matmul")

    # 移回 CPU
    z_cpu = z_npu.cpu()
    assert z_cpu.device.type == 'cpu'
    print(f"✓ Tensor moved back to CPU")

def test_nn_module():
    """验证神经网络模块"""
    model = torch.nn.Linear(10, 5)
    model_npu = model.to('npu')

    input_npu = torch.randn(2, 10).to('npu')
    output_npu = model_npu(input_npu)

    print(f"✓ NN module forward pass: output shape={output_npu.shape}")

def test_api_alignment():
    """验证与 torch.cuda API 对齐"""
    apis = [
        'is_available',
        'device_count',
        'current_device',
        'get_device_name',
        'synchronize',
    ]

    for api in apis:
        assert hasattr(torch.npu, api), f"torch.npu.{api} missing"
    print(f"✓ API alignment verified")

def test_privateuse1_backend():
    """验证 PrivateUse1 后端注册"""
    backend_name = torch.utils.backend_registration._get_privateuse1_backend_name()
    assert backend_name == 'npu', f"Backend name mismatch: {backend_name}"
    print(f"✓ PrivateUse1 backend registered as 'npu'")

def main():
    tests = [
        ("PyTorch Import", test_pytorch_import),
        ("torch_npu Import", test_torch_npu_import),
        ("NPU Device", test_npu_device),
        ("Tensor Operations", test_tensor_operations),
        ("NN Module", test_nn_module),
        ("API Alignment", test_api_alignment),
        ("PrivateUse1 Backend", test_privateuse1_backend),
    ]

    print("=" * 60)
    print("torch-npu Smoke Tests")
    print("=" * 60)

    passed, failed = 0, 0
    for name, test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
```

#### 4.4.4 Device-Agnostic Test 选择

推荐的 PyTorch 设备无关测试（参考 ROCm/XPU 模式）：

| 优先级 | 测试文件 | 说明 | 分片建议 |
|-------|---------|------|---------|
| **P0** | `test_torch.py` | 核心张量操作 | shard 1-2 |
| **P0** | `test_ops.py` | 算子测试（OpInfo） | shard 3-4 |
| **P1** | `test_nn.py` | 神经网络模块 | shard 5 |
| **P1** | `test_autograd.py` | 自动微分 | shard 6 |

#### 4.4.5 NPU Blocklist

```python
# 不在 NPU 上运行的测试

NPU_BLOCKLIST = [
    # 其他设备特有测试
    "test_cuda",
    "test_cuda_multigpu",
    "test_xpu",
    "test_mps",

    # 耗时过长（建议 Layer 4 或定时运行）
    "test_jit",
    "test_jit_profiling",

    # 需要多卡环境
    "distributed/test_c10d",
]
```

---

## 五、Workflow 设计

### 5.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    pytorch-infra Workflow 架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ pr-gate.yml (主入口)                                                    │ │
│  │                                                                         │ │
│  │   on: pull_request, workflow_dispatch                                  │ │
│  │                                                                         │ │
│  │   jobs:                                                                 │ │
│  │     ├── smoke-test         → Layer 1 (必须通过)                        │ │
│  │     ├── device-agnostic    → Layer 2 (Smoke 通过后)                    │ │
│  │     └── npu-specific       → Layer 3 (Device-Agnostic 通过后)          │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ nightly-integration.yml (每日定时)                                      │ │
│  │                                                                         │ │
│  │   on: schedule (每日 UTC 21:00)                                        │ │
│  │                                                                         │ │
│  │   jobs:                                                                 │ │
│  │     ├── full-test          → 全量测试                                   │ │
│  │     ├── distributed-test   → 分布式测试 (Layer 4)                       │ │
│  │     └── compatibility-report → 兼容性报告                               │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ issue-tracker.yml (自动追踪)                                             │ │
│  │                                                                         │ │
│  │   on: workflow_run (completed)                                         │ │
│  │                                                                         │ │
│  │   jobs:                                                                 │ │
│  │     ├── track-failure      → 创建兼容性 issue                           │ │
│  │     └── track-success      → 关闭已修复 issue                           │ │
│  │                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 PR Gate Workflow

```yaml
# pytorch-infra/.github/workflows/pr-gate.yml

name: torch-npu-pr-gate

on:
  repository_dispatch:
    types: [torch-npu-pr]
  workflow_dispatch:
    inputs:
      torch_npu_repo:
        description: 'torch-npu repository'
        required: true
        default: 'Ascend/pytorch'
      torch_npu_branch:
        description: 'torch-npu branch/ref'
        required: true
        default: 'master'
      torch_npu_sha:
        description: 'torch-npu commit SHA'
        required: true
      pr_number:
        description: 'PR number (for comment)'
        required: false

concurrency:
  group: pr-gate-${{ inputs.torch_npu_sha }}
  cancel-in-progress: true

env:
  PYTORCH_TESTING_DEVICE_ONLY_FOR: npu

jobs:
  smoke-test:
    runs-on: [self-hosted, npu-910b]
    timeout-minutes: 20
    outputs:
      pytorch_version: ${{ steps.version.outputs.pytorch_version }}
      torch_npu_sha: ${{ inputs.torch_npu_sha }}
      status: ${{ steps.test.outputs.status }}

    steps:
      - name: Checkout torch-npu
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.torch_npu_repo }}
          ref: ${{ inputs.torch_npu_sha }}
          submodules: recursive
          fetch-depth: 0

      - name: Setup NPU environment
        shell: bash
        run: |
          # 检查 NPU 设备
          npu-smi info

          # 设置设备权限
          sudo chmod 666 /dev/davinci* 2>/dev/null || true
          sudo chmod 666 /dev/davinci_manager 2>/dev/null || true

          # 设置环境变量
          echo "ASCEND_HOME=/usr/local/Ascend" >> $GITHUB_ENV
          source /usr/local/Ascend/bin/setenv.bash 2>/dev/null || true

      - name: Install PyTorch nightly
        id: version
        run: |
          pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu
          pip install numpy pyyaml

          # 记录版本
          PYTORCH_VER=$(python -c "import torch; print(torch.__version__)")
          PYTORCH_COMMIT=$(python -c "import torch; print(torch.__git_version__)")

          echo "pytorch_version=${PYTORCH_VER}" >> $GITHUB_OUTPUT
          echo "pytorch_commit=${PYTORCH_COMMIT}" >> $GITHUB_OUTPUT

          echo "### PyTorch Version Info" >> $GITHUB_STEP_SUMMARY
          echo "| Item | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| PyTorch Version | ${PYTORCH_VER} |" >> $GITHUB_STEP_SUMMARY
          echo "| PyTorch Commit | ${PYTORCH_COMMIT} |" >> $GITHUB_STEP_SUMMARY

      - name: Build torch-npu
        run: |
          python setup.py bdist_wheel
          pip install dist/torch_npu*.whl

      - name: Run Smoke Tests
        id: test
        run: |
          python test/smoke_test.py --verbose
          echo "status=success" >> $GITHUB_OUTPUT

      - name: Report to PR (if PR number provided)
        if: inputs.pr_number != ''
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.TORCH_NPU_TOKEN }}
          script: |
            const pr_number = '${{ inputs.pr_number }}';
            const repo = '${{ inputs.torch_npu_repo }}';
            const [owner, name] = repo.split('/');

            const body = `## 🔥 Smoke Test Results

            **Status**: ✅ Passed

            | Item | Value |
            |------|-------|
            | PyTorch nightly | `${{ steps.version.outputs.pytorch_version }}` |
            | torch-npu commit | `${{ inputs.torch_npu_sha }}` |
            | Test duration | ~2-5 min |

            ✅ Basic integration verified. Proceeding to full tests...`;

            github.rest.issues.createComment({
              owner: owner,
              repo: name,
              issue_number: parseInt(pr_number),
              body: body
            });

      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: smoke-test-failure
          path: |
            *.log
            test-reports/

  device-agnostic-test:
    needs: smoke-test
    if: needs.smoke-test.outputs.status == 'success'
    strategy:
      matrix:
        shard: [1, 2, 3, 4, 5, 6]
      fail-fast: false
    runs-on: [self-hosted, npu-910b]
    timeout-minutes: 45
    env:
      SHARD_NUMBER: ${{ matrix.shard }}
      NUM_TEST_SHARDS: 6

    steps:
      - name: Checkout torch-npu
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.torch_npu_repo }}
          ref: ${{ inputs.torch_npu_sha }}
          submodules: recursive

      - name: Setup NPU environment
        run: |
          npu-smi info
          sudo chmod 666 /dev/davinci* 2>/dev/null || true
          source /usr/local/Ascend/bin/setenv.bash 2>/dev/null || true

      - name: Install PyTorch nightly + torch-npu
        run: |
          pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu
          pip install dist/torch_npu*.whl || (python setup.py bdist_wheel && pip install dist/torch_npu*.whl)

      - name: Download PyTorch test suite
        run: |
          git clone --depth=1 https://github.com/pytorch/pytorch.git /tmp/pytorch

      - name: Run Device-Agnostic Tests (Shard ${{ matrix.shard }})
        run: |
          cd /tmp/pytorch
          export PYTHONPATH="$PWD:$PYTHONPATH"

          # 根据分片选择测试
          case ${{ matrix.shard }} in
            1|2) TESTS="test_torch" ;;
            3|4) TESTS="test_ops" ;;
            5)   TESTS="test_nn" ;;
            6)   TESTS="test_autograd" ;;
          esac

          python test/run_test.py \
            --include $TESTS \
            --npu \
            --shard ${{ matrix.shard }} 6

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: device-agnostic-shard-${{ matrix.shard }}
          path: /tmp/pytorch/test/test-reports/

  npu-specific-test:
    needs: device-agnostic-test
    if: success()
    runs-on: [self-hosted, npu-910b]
    timeout-minutes: 60

    steps:
      - name: Checkout torch-npu
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.torch_npu_repo }}
          ref: ${{ inputs.torch_npu_sha }}
          submodules: recursive

      - name: Setup NPU and install
        run: |
          npu-smi info
          source /usr/local/Ascend/bin/setenv.bash 2>/dev/null || true
          pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu
          pip install dist/torch_npu*.whl || (python setup.py bdist_wheel && pip install dist/torch_npu*.whl)
          pip install pytest pytest-xdist

      - name: Run NPU-specific tests
        run: |
          pytest test/ -v \
            --ignore=test/smoke/ \
            --ignore=test/distributed/ \
            -n auto \
            --tb=short

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: npu-specific-test-results
          path: test-reports/

  aggregate-results:
    needs: [smoke-test, device-agnostic-test, npu-specific-test]
    if: always()
    runs-on: ubuntu-latest
    outputs:
      final_status: ${{ steps.aggregate.outputs.status }}

    steps:
      - name: Aggregate results
        id: aggregate
        run: |
          smoke="${{ needs.smoke-test.result }}"
          da="${{ needs.device-agnostic-test.result }}"
          npu="${{ needs.npu-specific-test.result }}"

          if [[ "$smoke" == "success" && "$da" == "success" && "$npu" == "success" ]]; then
            echo "status=success" >> $GITHUB_OUTPUT
          else
            echo "status=failure" >> $GITHUB_OUTPUT
          fi

      - name: Final PR Comment
        if: inputs.pr_number != ''
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.TORCH_NPU_TOKEN }}
          script: |
            const status = '${{ steps.aggregate.outputs.status }}';
            const pr_number = '${{ inputs.pr_number }}';
            const repo = '${{ inputs.torch_npu_repo }}';
            const [owner, name] = repo.split('/');

            const emoji = status === 'success' ? '✅' : '❌';
            const body = `## ${emoji} torch-npu PR Gate Final Results

            **Status**: ${status === 'success' ? 'All tests passed' : 'Some tests failed'}

            | Test Layer | Status |
            |------------|--------|
            | Smoke Tests | ${needs.smoke-test.result === 'success' ? '✅' : '❌'} |
            | Device-Agnostic | ${needs.device-agnostic-test.result === 'success' ? '✅' : '❌'} |
            | NPU-Specific | ${needs.npu-specific-test.result === 'success' ? '✅' : '❌'} |

            **PyTorch nightly**: `${{ needs.smoke-test.outputs.pytorch_version }}`
            **torch-npu commit**: `${{ needs.smoke-test.outputs.torch_npu_sha }}`

            ${status === 'success'
              ? '🎉 PR is ready for merge.'
              : '⚠️ Please check the failed test logs.'}`;

            github.rest.issues.createComment({
              owner: owner,
              repo: name,
              issue_number: parseInt(pr_number),
              body: body
            });

      - name: Set GitHub Check status
        if: inputs.pr_number != ''
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.TORCH_NPU_TOKEN }}
          script: |
            const status = '${{ steps.aggregate.outputs.status }}';
            const repo = '${{ inputs.torch_npu_repo }}';
            const [owner, name] = repo.split('/');

            // Create commit status
            github.rest.repos.createCommitStatus({
              owner: owner,
              repo: name,
              sha: '${{ inputs.torch_npu_sha }}',
              state: status === 'success' ? 'success' : 'failure',
              context: 'pytorch-infra/pr-gate',
              description: status === 'success' ? 'All tests passed' : 'Tests failed',
              target_url: '${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}'
            });
```

### 5.3 torch-npu PR 触发配置

在 torch-npu 仓库中配置触发：

```yaml
# torch-npu/.github/workflows/trigger-integration.yml

name: trigger-pytorch-infra

on:
  pull_request:
    branches: [master, main]
    types: [opened, synchronize, reopened]

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger pytorch-infra integration test
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.PYTORCH_INFRA_TOKEN }}
          script: |
            github.rest.repos.createDispatchEvent({
              owner: 'computing-infra',  // pytorch-infra 仓库 owner
              repo: 'pytorch-infra',     // pytorch-infra 仓库名
              event_type: 'torch-npu-pr',
              client_payload: {
                torch_npu_repo: '${{ github.repository }}',
                torch_npu_branch: '${{ github.head_ref }}',
                torch_npu_sha: '${{ github.event.pull_request.head.sha }}',
                pr_number: '${{ github.event.pull_request.number }}'
              }
            });

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `🔄 Integration test triggered at [pytorch-infra](https://github.com/computing-infra/pytorch-infra)

              Testing torch-npu + PyTorch nightly...

              Results will be posted here when complete.`
            });
```

### 5.4 每日定时集成测试

```yaml
# pytorch-infra/.github/workflows/nightly-integration.yml

name: nightly-integration

on:
  schedule:
    - cron: '0 21 * * *'  # UTC 21:00 = 北京时间 05:00
  workflow_dispatch:

jobs:
  get-latest-versions:
    runs-on: ubuntu-latest
    outputs:
      torch_npu_sha: ${{ steps.torch_npu.outputs.sha }}
      pytorch_version: ${{ steps.pytorch.outputs.version }}

    steps:
      - name: Get torch-npu latest commit
        id: torch_npu
        run: |
          SHA=$(curl -s "https://api.github.com/repos/Ascend/pytorch/commits/master" | jq -r '.sha')
          echo "sha=${SHA}" >> $GITHUB_OUTPUT

      - name: Get PyTorch nightly version
        id: pytorch
        run: |
          VERSION=$(pip index versions torch --pre 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+\.dev\d+' || echo "nightly")
          echo "version=${VERSION}" >> $GITHUB_OUTPUT

  trigger-pr-gate:
    needs: get-latest-versions
    uses: ./.github/workflows/pr-gate.yml
    with:
      torch_npu_repo: 'Ascend/pytorch'
      torch_npu_branch: 'master'
      torch_npu_sha: ${{ needs.get-latest-versions.outputs.torch_npu_sha }}
      pr_number: ''

  create-compatibility-report:
    needs: [get-latest-versions, trigger-pr-gate]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Create compatibility report
        run: |
          mkdir -p reports
          cat > reports/compatibility_report.md << EOF
          # torch-npu + PyTorch Nightly Compatibility Report

          **Date**: $(date -u +"%Y-%m-%d")

          | Component | Version |
          |-----------|---------|
          | PyTorch nightly | ${{ needs.get-latest-versions.outputs.pytorch_version }} |
          | torch-npu | ${{ needs.get-latest-versions.outputs.torch_npu_sha }} |
          | Test Status | ${{ needs.trigger-pr-gate.outputs.final_status }} |

          EOF

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: compatibility-report-$(date -u +"%Y-%m-%d")
          path: reports/
```

---

## 六、Issue 追踪机制

### 6.1 兼容性问题追踪

```yaml
# pytorch-infra/.github/workflows/issue-tracker.yml

name: issue-tracker

on:
  workflow_run:
    workflows: ["torch-npu-pr-gate"]
    types: [completed]

jobs:
  track-failure:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - name: Create compatibility issue in torch-npu
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.TORCH_NPU_TOKEN }}
          script: |
            const run = context.payload.workflow_run;
            const payload = run.inputs || {};

            // 检查是否已存在相同 issue
            const issues = await github.rest.issues.listForRepo({
              owner: 'Ascend',
              repo: 'pytorch',
              state: 'open',
              labels: 'compatibility'
            });

            const sha_short = (payload.torch_npu_sha || run.head_sha).slice(0, 7);
            const existing = issues.data.find(i =>
              i.title.includes(sha_short) &&
              i.body.includes('PyTorch nightly')
            );

            if (!existing && payload.torch_npu_sha) {
              await github.rest.issues.create({
                owner: 'Ascend',
                repo: 'pytorch',
                title: `[Compatibility] Integration test failed: ${sha_short}`,
                body: `
## 失败信息

- **torch-npu commit**: ${payload.torch_npu_sha}
- **PyTorch nightly**: latest
- **Workflow run**: [View logs](https://github.com/${run.repository.full_name}/actions/runs/${run.id})

## 分析建议

1. 检查 PyTorch nightly API 变更
2. 确认 torch-npu 代码是否需要适配
3. 参考: https://github.com/pytorch/pytorch/releases

## Labels

请添加适当的标签: `compatibility`, `ci-failure`
                `,
                labels: ['compatibility', 'ci-failure']
              });
            }

  track-success:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - name: Close fixed compatibility issues
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.TORCH_NPU_TOKEN }}
          script: |
            const run = context.payload.workflow_run;
            const payload = run.inputs || {};

            if (!payload.torch_npu_sha) return;

            const sha_short = payload.torch_npu_sha.slice(0, 7);

            // 查找相关 issue
            const issues = await github.rest.issues.listForRepo({
              owner: 'Ascend',
              repo: 'pytorch',
              state: 'open',
              labels: 'compatibility'
            });

            for (const issue of issues.data) {
              if (issue.title.includes(sha_short)) {
                await github.rest.issues.update({
                  owner: 'Ascend',
                  repo: 'pytorch',
                  issue_number: issue.number,
                  state: 'closed',
                  body: issue.body + '\n\n---\n✅ Fixed by ' + payload.torch_npu_sha
                });

                await github.rest.issues.createComment({
                  owner: 'Ascend',
                  repo: 'pytorch',
                  issue_number: issue.number,
                  body: `✅ Integration test passed. Issue closed.`
                });
              }
            }
```

---

## 七、Runner 环境配置

### 7.1 Runner 类型

| Runner 类型 | NPU 数量 | 用途 | 配置建议 |
|------------|---------|------|---------|
| `self-hosted, npu-910b` | 1 | PR 测试 | 910B 单卡 |
| `self-hosted, npu-910b-4` | 4 | 分布式测试 | 910B 4卡 |
| `self-hosted, npu-910a` | 1 | 多架构测试 | 910A 单卡 |

### 7.2 Runner 环境准备

```bash
# Runner 主机环境配置脚本

#!/bin/bash

# 1. 安装 NPU 驱动和 CANN
# 参考: https://www.hiascend.com/document

# 2. 安装 Docker
apt-get update
apt-get install -y docker.io

# 3. 配置 NPU 设备权限
cat > /etc/rc.local << 'EOF'
chmod 666 /dev/davinci* 2>/dev/null || true
chmod 666 /dev/davinci_manager 2>/dev/null || true
chmod 666 /dev/devmm_svm 2>/dev/null || true
chmod 666 /dev/hisi_hdc 2>/dev/null || true
EOF

# 4. 安装 GitHub Actions Runner
mkdir -p /actions-runner
cd /actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-*.tar.gz

# 5. 配置 Runner
./config.sh --url https://github.com/computing-infra/pytorch-infra \
  --token <RUNNER_TOKEN> \
  --labels npu-910b

# 6. 启动 Runner
./run.sh
```

### 7.3 华为云 CCI 方案（可选）

如使用华为云 CCI (Container Instance)：

```yaml
# 使用华为云 CCI runner

jobs:
  smoke-test:
    runs-on: cci-npu-910b  # 华为云 CCI runner label
    container:
      image: swr.cn-east-3.myhuaweicloud.com/ascend/pytorch:latest
      options: --device=/dev/davinci0 --privileged
```

---

## 八、实施路线图

### 8.1 Phase 1: PR 集成验证（Week 1-2）

```
目标: torch-npu PR + PyTorch nightly 集成验证

任务清单:
├── 1. 配置 Runner 环境
│   ├── 申请 NPU 资源（华为云或自托管）
│   ├── 安装 CANN 和驱动
│   ├── 配置 GitHub Actions Runner
│   └── 验证 NPU 设备可用性
│
├── 2. 创建 pr-gate.yml
│   ├── Smoke Test job
│   ├── PyTorch nightly 安装流程
│   ├── torch-npu 构建流程
│   ├── 结果报告机制
│
├── 3. torch-npu 配置触发
│   ├── 创建 trigger-integration.yml
│   ├── 配置 repository_dispatch
│   ├── 配置 PR comment 机制
│
├── 4. 编写 smoke_test.py
│   ├── 基本导入验证
│   ├── NPU 设备检测
│   ├── 张量操作验证
│   ├── API 对齐检查
│
└── 5. 验证整体流程
    ├── 提交测试 PR
    ├── 检查触发流程
    ├── 验证结果报告
    └── 调整超时和配置

验收标准:
✅ torch-npu PR 能自动触发测试
✅ 15 分钟内完成 Smoke 测试
✅ 结果正确报告到 PR comment
✅ GitHub Check 状态正确设置
```

### 8.2 Phase 2: 设备无关测试（Week 3-4）

```
目标: 扩展到 PyTorch 设备无关测试

任务清单:
├── 1. 扩展 pr-gate.yml
│   ├── 添加 device-agnostic-test job
│   ├── 配置测试分片
│   ├── 复用 PyTorch test/run_test.py
│
├── 2. 配置 NPU 测试基类
│   ├── NPUTestBase 实现
│   ├── 环境变量设置
│   ├── Blocklist 配置
│
├── 3. 优化测试效率
│   ├── 并行分片执行
│   ├── 测试缓存策略
│   ├── 失败重试机制
│
└── 4. 结果聚合
    ├── 多分片结果合并
    ├── 统计报告生成
    ├── PR 状态更新

验收标准:
✅ 6 分片并行执行
✅ 30 分钟内完成设备无关测试
✅ PyTorch 核心测试通过率 > 90%
```

### 8.3 Phase 3: NPU 专用测试（Week 5-6）

```
目标: 完整 torch-npu 测试覆盖

任务清单:
├── 1. 添加 npu-specific-test job
│   ├── torch-npu 测试集成
│   ├── pytest 并行配置
│   ├── 测试分类整理
│
├── 2. 每日定时测试
│   ├── nightly-integration.yml
│   ├── 兼容性报告生成
│   ├── 结果历史追踪
│
└── 3. Issue 追踪
    ├── issue-tracker.yml
    ├── 失败自动创建 issue
    ├── 修复自动关闭 issue

验收标准:
✅ torch-npu 专用测试全部通过
✅ 每日定时测试运行
✅ Issue 自动追踪机制运行
```

### 8.4 Phase 4: 扩展测试（Week 7+）

```
目标: 分布式测试和性能基准

任务清单:
├── 1. 分布式测试
│   ├── 多卡 runner 配置
│   ├── HCCL 测试集成
│   ├── distributed job
│
├── 2. Inductor 测试
│   ├── Triton-NPU 支持
│   ├── 编译器测试
│   ├── 性能基准
│
└── 3. 多架构支持
    ├── 910A runner
    ├── 310P runner
    ├── 架构矩阵测试

验收标准:
✅ 分布式测试每日运行
✅ Inductor 测试集成完成
✅ 多架构测试支持
```

---

## 九、附录

### 9.1 环境变量汇总

```bash
# torch-npu + PyTorch 集成测试环境变量

# 设备类型
export PYTORCH_TESTING_DEVICE_ONLY_FOR="npu"

# CANN 路径
export ASCEND_HOME=/usr/local/Ascend
export ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit

# 测试配置
export SHARD_NUMBER=1
export NUM_TEST_SHARDS=6

# NPU 架构
export NPU_ARCH="Ascend910B"
```

### 9.2 PyTorch nightly 版本获取

```bash
# 方式 1: pip 安装 nightly
pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu

# 方式 2: 指定版本
pip install torch==2.7.0.dev20250330 --index-url https://download.pytorch.org/whl/nightly/cpu

# 方式 3: 从源码构建（备用）
git clone --depth=1 --branch=main https://github.com/pytorch/pytorch.git
cd pytorch && python setup.py install
```

### 9.3 与其他设备测试对比

| 特性 | CUDA (主仓) | ROCm (主仓) | XPU (主仓) | **NPU (中间CI)** |
|------|------------|------------|-----------|------------------|
| 代码位置 | PyTorch 主仓 | PyTorch 主仓 | PyTorch 主仓 | torch-npu 独立仓库 |
| 触发方式 | PR + 定时 | 定时 + tag | 定时 + tag | **PR + 定时** |
| PyTorch 版本 | 主仓代码 | 主仓代码 | 主仓代码 | **nightly wheel** |
| Smoke 测试 | test_cuda | test_transformers | smoke_xpu | **smoke_test.py** |
| 设备无关测试 | trunk.yml 分片 | 6 分片 | 6-12 分片 | **6 分片** |
| 反馈方式 | GitHub Check | PR label | PR label | **PR Comment + Check** |

### 9.4 常见问题处理

| 问题 | 解决方案 |
|------|---------|
| PyTorch nightly API 变更导致失败 | 1. 检查变更内容<br>2. 适配 torch-npu 代码<br>3. 更新测试 |
| NPU 设备不可用 | 1. 检查驱动状态<br>2. 检查设备权限<br>3. 检查 CANN 环境 |
| 构建超时 | 1. 使用预构建 wheel<br>2. 配置 ccache<br>3. 减少编译范围 |
| 测试不稳定 | 1. 标记 flaky test<br>2. 配置重试策略<br>3. 独立追踪 |

### 9.5 参考资料

- PyTorch 官方 CI: https://github.com/pytorch/pytorch/tree/main/.github/workflows
- ROCm 门禁: `rocm-mi300.yml`, `_rocm-test.yml`
- XPU 门禁: `xpu.yml`, `_xpu-test.yml`
- PrivateUse1 机制: `torch/testing/_internal/common_device_type.py`
- CANN 文档: https://www.hiascend.com/document
- torch-npu 仓库: https://gitcode.com/Ascend/pytorch