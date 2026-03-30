# Ascend NPU CI/CD 门禁方案开发计划

本文档将 `02-ascend-npu-ci-image-gate-design.md` 方案拆解为可独立验证的开发任务。

---

## 开发阶段概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        开发阶段总览                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 0: 基础设施搭建（Week 1-2）                                            │
│  ─────────────────────────────                                             │
│  目标: 镜像体系 + 构建流程 + Runner 环境                                       │
│  任务数: 19                                                                 │
│  阻塞点: NPU 资源申请                                                         │
│                                                                             │
│  Phase 1: PR 集成验证（Week 3-4）                                             │
│  ─────────────────────────────                                             │
│  目标: torch-npu PR 自动触发测试                                              │
│  任务数: 12                                                                 │
│  依赖: Phase 0 完成                                                          │
│                                                                             │
│  Phase 2: 设备无关测试（Week 5-6）                                             │
│  ─────────────────────────────                                             │
│  目标: PyTorch 通用测试在 NPU 上运行                                           │
│  任务数: 8                                                                  │
│  依赖: Phase 1 Smoke 测试通过                                                 │
│                                                                             │
│  Phase 3: NPU 专用测试（Week 7-8）                                            │
│  ─────────────────────────────                                             │
│  目标: torch-npu 专用测试 + 每日定时                                           │
│  任务数: 6                                                                  │
│  依赖: Phase 2 完成                                                          │
│                                                                             │
│  Phase 4: 扩展功能（Week 9+）                                                 │
│  ─────────────────────────────                                             │
│  目标: 分布式测试 + 多架构 + 性能基准                                           │
│  任务数: TBD                                                                │
│  依赖: Phase 3 稳定运行                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: 基础设施搭建

### 0.1 镜像体系设计

#### Task 0.1.1: 创建镜像仓库命名空间

**描述**: 在 ghcr、quay.io、SWR 三个仓库创建命名空间

**工作内容**:
```bash
# ghcr.io - GitHub 组织自动提供
# 确保 computing-infra 组织存在

# quay.io
# 1. 登录 quay.io
# 2. 创建 organization: ascendpytorch
# 3. 创建 repository: ascend-ci

# 华为云 SWR
# 1. 登录华为云控制台
# 2. SWR → 组织管理 → 创建组织: ascend-ci
# 3. 创建镜像仓库目录结构
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| ghcr.io 命名空间 | 可以推送镜像到 `ghcr.io/computing-infra/ascend-ci/` |
| quay.io 组织 | 可以推送镜像到 `quay.io/ascendpytorch/ascend-ci/` |
| SWR 组织 | 可以推送镜像到 `swr.cn-east-3.myhuaweicloud.com/ascend-ci/` |

**预计工时**: 0.5 天

---

#### Task 0.1.2: 配置仓库访问凭证

**描述**: 在 GitHub Secrets 中配置三个仓库的访问凭证

**工作内容**:
```yaml
# GitHub Secrets 配置
# Repository: computing-infra/pytorch-infra
# Settings → Secrets and variables → Actions → New repository secret

secrets:
  # ghcr.io（GITHUB_TOKEN 自动提供，无需配置）

  # quay.io
  QUAY_USERNAME: "ascendpytorch+robot_account_name"
  QUAY_PASSWORD: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

  # 华为云 SWR
  SWR_USERNAME: "cn-east-3@AKxxxxxxxxxxxx"
  SWR_PASSWORD: "SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| quay.io 登录 | `docker login quay.io -u $QUAY_USERNAME -p $QUAY_PASSWORD` 成功 |
| SWR 登录 | `docker login swr.cn-east-3.myhuaweicloud.com` 成功 |
| GitHub Secrets | Workflow 中 `${{ secrets.QUAY_USERNAME }}` 可读取 |

**预计工时**: 0.5 天

---

#### Task 0.1.3: 创建 Dockerfile 目录结构

**描述**: 在仓库中创建 Dockerfile 目录和文件（借鉴 PyTorch `.ci/docker/` 模块化设计）

**背景说明**:

PyTorch 官方镜像构建采用模块化设计，将安装逻辑拆分为独立脚本：
- `.ci/docker/common/install_base.sh` - 基础工具安装
- `.ci/docker/common/install_conda.sh` - Python 环境
- `.ci/docker/common/install_cuda.sh` - CUDA 安装
- `.ci/docker/common/install_rocm.sh` - ROCm 安装

我们借鉴此设计，创建 `dockerfiles/common/` 目录存放模块化安装脚本。

**工作内容**:
```bash
# 创建镜像目录
mkdir -p dockerfiles/{base-npu,cann-npu,runner-npu,test-npu}

# 创建模块化脚本目录（借鉴 PyTorch）
mkdir -p dockerfiles/common

# 创建 Dockerfile 文件
touch dockerfiles/base-npu/Dockerfile
touch dockerfiles/cann-npu/Dockerfile
touch dockerfiles/runner-npu/Dockerfile
touch dockerfiles/test-npu/Dockerfile

# 创建模块化安装脚本
touch dockerfiles/common/install_base.sh
touch dockerfiles/common/install_python.sh
touch dockerfiles/common/install_cann.sh
touch dockerfiles/common/install_hccl.sh
touch dockerfiles/common/install_runner.sh
touch dockerfiles/common/common_utils.sh

# 创建其他文件
touch dockerfiles/cann-npu/packages/.gitkeep
touch dockerfiles/runner-npu/entrypoint.sh
chmod +x dockerfiles/runner-npu/entrypoint.sh
```

**目录结构**:
```
dockerfiles/
├── base-npu/
│   └── Dockerfile              # 基础镜像
├── cann-npu/
│   ├── Dockerfile              # CANN 镜像
│   └── packages/               # CANN 安装包目录
├── runner-npu/
│   ├── Dockerfile              # Runner 镜像
│   └── entrypoint.sh           # Runner 入口脚本
├── test-npu/
│   └── Dockerfile              # 测试镜像
└── common/                      # 模块化安装脚本（借鉴 PyTorch）
    ├── install_base.sh         # 基础工具安装
    ├── install_python.sh       # Python 安装
    ├── install_cann.sh         # CANN 安装
    ├── install_hccl.sh         # HCCL 安装
    ├── install_runner.sh       # Runner 安装
    └── common_utils.sh         # 公共函数
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 镜像目录 | `ls dockerfiles/base-npu dockerfiles/cann-npu dockerfiles/runner-npu dockerfiles/test-npu` |
| common 目录 | `ls dockerfiles/common/` 显示 6 个脚本文件 |
| Dockerfile 存在 | 4 个 Dockerfile 文件都存在 |
| 脚本可执行 | `ls -la dockerfiles/common/*.sh` 显示正确权限 |

**预计工时**: 0.5 天

---

### 0.2 模块化脚本开发

#### Task 0.2.0: 编写公共安装脚本

**描述**: 创建模块化安装脚本，供 Dockerfile 调用

**设计原则**:
- 参考 PyTorch `.ci/docker/common/` 脚本结构
- 每个脚本独立可测试
- 支持参数化配置（版本号、路径等）

**工作内容**:

**1. common_utils.sh - 公共函数**
```bash
#!/bin/bash
# dockerfiles/common/common_utils.sh

set -ex

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 not found"
        exit 1
    fi
    log_info "$1 found: $(command -v $1)"
}

# 清理 apt 缓存
cleanup_apt() {
    apt-get clean
    rm -rf /var/lib/apt/lists/*
}
```

**2. install_base.sh - 基础工具安装**
```bash
#!/bin/bash
# dockerfiles/common/install_base.sh
# 参考 PyTorch .ci/docker/common/install_base.sh

set -ex

source common_utils.sh

install_ubuntu() {
    log_info "Installing base packages on Ubuntu..."

    apt-get update

    # 构建工具
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        pkg-config

    # 版本控制和网络
    apt-get install -y --no-install-recommends \
        git \
        curl \
        wget \
        ca-certificates

    # 开发库
    apt-get install -y --no-install-recommends \
        libssl-dev \
        libyaml-dev \
        libz-dev \
        libffi-dev

    # 缓存和工具
    apt-get install -y --no-install-recommends \
        ccache \
        jq \
        sudo \
        vim \
        gdb \
        bc

    cleanup_apt

    log_info "Base packages installed successfully"
}

install_ubuntu
```

**3. install_python.sh - Python 安装**
```bash
#!/bin/bash
# dockerfiles/common/install_python.sh
# 安装系统 Python（非 Conda，更适合 CANN 环境）

set -ex

source common_utils.sh

PYTHON_VERSION=${1:-3.11}

install_python() {
    log_info "Installing Python ${PYTHON_VERSION}..."

    # 添加 deadsnakes PPA
    apt-get update
    apt-get install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa

    # 安装 Python
    apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-dev \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-distutils

    cleanup_apt

    # 创建符号链接
    ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3
    ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python

    # 安装 pip
    curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION}

    log_info "Python ${PYTHON_VERSION} installed: $(python --version)"
}

install_python
```

**4. install_cann.sh - CANN 安装**
```bash
#!/bin/bash
# dockerfiles/common/install_cann.sh

set -ex

source common_utils.sh

CANN_VERSION=${1:-8.0.RC1}
CANN_INSTALL_PATH=${2:-/usr/local/Ascend}

install_cann() {
    log_info "Installing CANN ${CANN_VERSION}..."

    # 检查安装包
    CANN_PKG="/tmp/Ascend-cann-toolkit_${CANN_VERSION}_linux-x86_64.run"

    if [[ ! -f "$CANN_PKG" ]]; then
        log_error "CANN package not found: $CANN_PKG"
        log_info "Please download from: https://www.hiascend.com/developer/download/community"
        exit 1
    fi

    # 安装
    chmod +x $CANN_PKG
    mkdir -p ${CANN_INSTALL_PATH}
    $CANN_PKG --install --install-path=${CANN_INSTALL_PATH}

    # 设置环境变量
    echo "source ${CANN_INSTALL_PATH}/bin/setenv.bash" >> /etc/bash.bashrc

    log_info "CANN ${CANN_VERSION} installed to ${CANN_INSTALL_PATH}"
}

install_cann
```

**5. install_runner.sh - GitHub Runner 安装**
```bash
#!/bin/bash
# dockerfiles/common/install_runner.sh

set -ex

source common_utils.sh

RUNNER_VERSION=${1:-2.311.0}
RUNNER_USER=${2:-runner}

install_runner() {
    log_info "Installing GitHub Actions Runner ${RUNNER_VERSION}..."

    # 创建用户
    useradd -m -s /bin/bash ${RUNNER_USER}

    # 下载 Runner
    RUNNER_DIR=/home/${RUNNER_USER}
    cd ${RUNNER_DIR}

    curl -o actions-runner.tar.gz -L \
        https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

    tar xzf actions-runner.tar.gz
    rm actions-runner.tar.gz

    # 安装依赖
    ./bin/installdependencies.sh

    # 设置权限
    chown -R ${RUNNER_USER}:${RUNNER_USER} ${RUNNER_DIR}

    log_info "GitHub Runner ${RUNNER_VERSION} installed to ${RUNNER_DIR}"
}

install_runner
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| common_utils.sh | `bash -n dockerfiles/common/common_utils.sh` 无语法错误 |
| install_base.sh | 在 Ubuntu 容器中测试执行 |
| install_python.sh | 测试安装后 `python --version` 显示正确版本 |
| 脚本权限 | 所有脚本有执行权限 |

**预计工时**: 1 天

---

### 0.3 Base Image 构建

#### Task 0.3.1: 编写 Base Image Dockerfile

**描述**: 创建 Ubuntu 22.04 + Python 3.11 基础镜像 Dockerfile（借鉴 PyTorch 模块化设计）

**背景说明**:

参考 PyTorch `.ci/docker/ubuntu/Dockerfile` 设计：
- 使用 `ARG` 参数化版本
- 调用 `common/` 目录下的模块化脚本
- 设置 `BUILD_ENVIRONMENT` 环境变量标识

**工作内容**:
```dockerfile
# dockerfiles/base-npu/Dockerfile
# 参考 PyTorch .ci/docker/ubuntu/Dockerfile 设计
# 使用系统 Python（非 Conda），更适合 CANN 环境

ARG UBUNTU_VERSION=22.04
FROM ubuntu:${UBUNTU_VERSION} as base

ENV DEBIAN_FRONTEND=noninteractive

# 允许 APT 以 root 运行（借鉴 PyTorch）
RUN echo 'APT::Sandbox::User "root";' | tee -a /etc/apt/apt.conf.d/10sandbox

# 复制安装脚本
COPY common/install_base.sh /tmp/install_base.sh
COPY common/install_python.sh /tmp/install_python.sh
COPY common/common_utils.sh /tmp/common_utils.sh

# 安装基础依赖
RUN cd /tmp && bash ./install_base.sh && rm -f install_base.sh

# 安装 Python
ARG PYTHON_VERSION=3.11
RUN cd /tmp && bash ./install_python.sh ${PYTHON_VERSION} && rm -f install_python.sh common_utils.sh

# 配置 ccache
ENV CCACHE_DIR=/cache/ccache
ENV CCACHE_MAXSIZE=5G
RUN mkdir -p /cache/ccache /cache/pip

# 设置 PATH
ENV PATH="/usr/local/bin:/usr/bin:${PATH}"

# 创建工作目录
WORKDIR /workspace

# 设置镜像标识（借鉴 PyTorch BUILD_ENVIRONMENT）
ARG BUILD_ENVIRONMENT=base-npu
ENV BUILD_ENVIRONMENT=${BUILD_ENVIRONMENT}

# 版本信息
RUN python --version && pip --version
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 本地构建成功 | `docker build -t base-npu:test dockerfiles/base-npu/` 成功 |
| Python 版本 | `docker run base-npu:test python --version` 显示 3.11.x |
| pip 可用 | `docker run base-npu:test pip --version` 成功 |
| ccache 可用 | `docker run base-npu:test ccache --version` 成功 |
| BUILD_ENVIRONMENT | `docker run base-npu:test env \| grep BUILD_ENVIRONMENT` 显示 base-npu |
| 镜像大小 | < 500MB |

**预计工时**: 1 天

---

#### Task 0.3.2: 创建 Base Image 构建 Workflow

**描述**: 创建 `.github/workflows/build-base-image.yml`

**工作内容**:
```yaml
# 触发方式: workflow_dispatch + schedule(每6月)
# 输入: ubuntu_version, python_version
# 输出: base-npu:ubuntu22.04-py311-[date]
# 推送: ghcr + swr
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在 `.github/workflows/` 目录下 |
| 手动触发成功 | Actions 页面可以手动触发并成功完成 |
| 镜像推送到 ghcr | `ghcr.io/computing-infra/ascend-ci/base-npu:latest` 存在 |
| 镜像推送到 swr | `swr.cn-east-3.myhuaweicloud.com/ascend-ci/base-npu:latest` 存在 |
| 镜像可拉取 | `docker pull ghcr.io/computing-infra/ascend-ci/base-npu:latest` 成功 |

**预计工时**: 1 天

---

### 0.4 CANN Image 构建

#### Task 0.4.1: 编写 CANN Image Dockerfile

**描述**: 创建包含 CANN Toolkit 的镜像 Dockerfile

**工作内容**:
```dockerfile
# dockerfiles/cann-npu/Dockerfile
ARG BASE_IMAGE=base-npu:latest
FROM ${BASE_IMAGE}

# 复制 CANN 安装包（需提前下载）
COPY packages/*.run /tmp/

# 复制安装脚本
COPY common/install_cann.sh /tmp/install_cann.sh
COPY common/install_hccl.sh /tmp/install_hccl.sh
COPY common/common_utils.sh /tmp/common_utils.sh

# 安装 CANN
ARG CANN_VERSION=8.0.RC1
RUN cd /tmp && bash ./install_cann.sh ${CANN_VERSION} && rm -f install_cann.sh

# 设置 CANN 环境变量
ENV ASCEND_HOME=/usr/local/Ascend
ENV ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit
ENV PATH="${ASCEND_TOOLKIT_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${ASCEND_TOOLKIT_HOME}/lib64:${LD_LIBRARY_PATH}"
```

**前置条件**: Task 0.3.1 完成，有可用的 Base Image

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 本地构建成功（有 CANN 包） | `docker build -t cann-npu:test dockerfiles/cann-npu/` 成功 |
| CANN 环境变量 | `docker run cann-npu:test env | grep ASCEND` 显示正确路径 |
| Python 可导入 te | `docker run cann-npu:test python -c "import te"` 成功（或输出安装信息） |

**预计工时**: 1 天

**阻塞点**: 需要 CANN 安装包下载地址或本地缓存

---

#### Task 0.4.2: 创建 CANN Image 构建 Workflow

**描述**: 创建 `.github/workflows/build-cann-image.yml`

**工作内容**:
```yaml
# 触发方式: workflow_dispatch + repository_dispatch
# 输入: cann_version, npu_arch
# 输出: cann-npu:[version]-[arch]
# 推送: 仅 swr（华为生态）
# 触发下游: runner-image 构建
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| 手动触发成功 | 指定 CANN 8.0.RC1，构建成功 |
| 镜像推送到 swr | `swr.cn-east-3.myhuaweicloud.com/ascend-ci/cann-npu:8.0.RC1-910B` 存在 |
| 触发下游构建 | 构建成功后触发 runner-image workflow |

**预计工时**: 1 天

---

### 0.5 Runner Image 构建

#### Task 0.5.1: 编写 Runner Image Dockerfile

**描述**: 创建包含 GitHub Actions Runner 的镜像 Dockerfile

**工作内容**:
```dockerfile
# dockerfiles/runner-npu/Dockerfile
ARG CANN_IMAGE=cann-npu:latest
FROM ${CANN_IMAGE}

# 安装 GitHub Actions Runner
# 安装测试工具: pytest, pytest-xdist
# 创建 runner 用户
```

**前置条件**: Task 0.4.1 完成，有可用的 CANN Image

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 本地构建成功 | `docker build -t runner-npu:test dockerfiles/runner-npu/` 成功 |
| Runner 文件存在 | `docker run runner-npu:test ls /home/runner/` 显示 runner 文件 |
| pytest 可用 | `docker run runner-npu:test pytest --version` 成功 |

**预计工时**: 1 天

---

#### Task 0.5.2: 编写 Runner entrypoint 脚本

**描述**: 创建 Runner 启动入口脚本

**工作内容**:
```bash
# dockerfiles/runner-npu/entrypoint.sh
#!/bin/bash
# 设置 NPU 设备权限
# 设置 CANN 环境
# Runner 注册逻辑
# 启动 Runner
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 脚本可执行 | `chmod +x entrypoint.sh` 后 `./entrypoint.sh` 可运行 |
| 环境变量设置 | 脚本中包含 `source /usr/local/Ascend/bin/setenv.bash` |
| Runner 启动逻辑 | 脚本中包含 `./run.sh` |

**预计工时**: 0.5 天

---

#### Task 0.5.3: 创建 Runner Image 构建 Workflow

**描述**: 创建 `.github/workflows/build-runner-image.yml`

**工作内容**:
```yaml
# 触发方式: workflow_dispatch + repository_dispatch + schedule
# 输入: cann_image, runner_version
# 输出: runner-npu:cann[ver]-runner[ver]-[date]
# 推送: ghcr + swr
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| 手动触发成功 | 指定 cann_image，构建成功 |
| 镜像推送到 ghcr | `ghcr.io/computing-infra/ascend-ci/runner-npu:*` 存在 |
| 镜像推送到 swr | `swr.cn-east-3.myhuaweicloud.com/ascend-ci/runner-npu:*` 存在 |

**预计工时**: 1 天

---

### 0.6 Test Image 构建

#### Task 0.6.1: 编写 Test Image Dockerfile

**描述**: 创建包含 PyTorch + torch-npu 的测试镜像 Dockerfile

**工作内容**:
```dockerfile
# dockerfiles/test-npu/Dockerfile
ARG RUNNER_IMAGE=runner-npu:latest
FROM ${RUNNER_IMAGE}

# 安装 PyTorch nightly
# 克隆并构建 torch-npu
# 安装测试依赖
```

**前置条件**: Task 0.5.1 完成，有可用的 Runner Image

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 本地构建成功（无 NPU） | `docker build -t test-npu:test dockerfiles/test-npu/` 成功 |
| PyTorch 可导入 | `docker run test-npu:test python -c "import torch"` 成功 |
| PyTorch 版本 | 显示 nightly 版本号 |

**预计工时**: 1 天

---

#### Task 0.6.2: 创建 Test Image 构建 Workflow

**描述**: 创建 `.github/workflows/build-test-image.yml`

**工作内容**:
```yaml
# 触发方式: workflow_dispatch + schedule(每日) + repository_dispatch
# 输入: pytorch_version, cann_version, torch_npu_commit
# 输出: test-npu:py[ver]-cann[ver]-[date]
# 推送: ghcr + swr + quay
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| 手动触发成功 | 指定 pytorch_version，构建成功 |
| 镜像推送到 ghcr | `ghcr.io/computing-infra/ascend-ci/test-npu:*` 存在 |
| 镜像推送到 swr | `swr.cn-east-3.myhuaweicloud.com/ascend-ci/test-npu:*` 存在 |
| 镜像推送到 quay | `quay.io/ascendpytorch/ascend-ci/test-npu:*` 存在 |
| 每日构建触发 | 每日 UTC 06:00 自动执行 |

**预计工时**: 1 天

---

### 0.7 兼容性矩阵管理

#### Task 0.7.1: 创建兼容性矩阵文件

**描述**: 创建 `compatibility_matrix.json` 文件用于记录版本兼容关系

**工作内容**:
```json
{
  "version_matrix": [],
  "metadata": {
    "last_updated": "",
    "source": ""
  }
}
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 文件存在 | `compatibility_matrix.json` 在仓库根目录 |
| JSON 格式正确 | `jq . compatibility_matrix.json` 成功 |
| 结构符合设计 | 包含 version_matrix 和 metadata 字段 |

**预计工时**: 0.5 天

---

#### Task 0.7.2: 创建兼容性验证 Workflow

**描述**: 创建 `.github/workflows/verify-compatibility.yml`

**工作内容**:
```yaml
# 触发方式: repository_dispatch(test-image-built) + workflow_dispatch
# 运行环境: self-hosted, npu-910b
# 步骤: 拉取镜像 → 设置NPU → 运行Smoke测试 → 更新兼容矩阵
```

**前置条件**: 有可用的 NPU Runner

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| Smoke 测试执行 | 在 NPU Runner 上成功运行 |
| 兼容矩阵更新 | 构建成功后 compatibility_matrix.json 有新条目 |

**预计工时**: 1 天

---

### 0.8 镜像清理

#### Task 0.8.1: 创建镜像清理 Workflow

**描述**: 创建 `.github/workflows/cleanup-images.yml`

**工作内容**:
```yaml
# 触发方式: schedule(每日 03:00 UTC) + workflow_dispatch
# 功能: 检查镜像年龄 → 应用保留策略 → 删除过期镜像
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| 手动触发成功 | Workflow 执行成功（dry_run 模式） |
| 清理日志 | Step Summary 显示清理统计 |

**预计工时**: 0.5 天

---

### 0.9 Runner 环境配置

#### Task 0.9.1: 申请 NPU 资源

**描述**: 申请 NPU Runner 运行所需的硬件资源

**工作内容**:
```
1. 确定资源方案:
   - 方案A: 自托管物理机（申请 910B 单卡）
   - 方案B: 华为云 CCI（申请 NPU 容器实例）
   - 方案C: 华为云 ECS + NPU（申请云服务器）

2. 提交资源申请
3. 等待资源到位
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| NPU 设备可用 | `npu-smi info` 显示设备信息 |
| 驱动已安装 | NPU 驱动版本显示正常 |
| CANN 已安装 | `cat /usr/local/Ascend/version.info` 存在 |

**预计工时**: 取决于审批流程

**阻塞点**: 这是整个项目的关键阻塞点

---

#### Task 0.9.2: 安装 GitHub Actions Runner

**描述**: 在 NPU 机器上安装和配置 GitHub Actions Runner

**工作内容**:
```bash
# 方式1: 直接安装（物理机）
mkdir -p /actions-runner
cd /actions-runner
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf actions-runner.tar.gz
./config.sh --url https://github.com/computing-infra/pytorch-infra --token <TOKEN> --labels npu-910b
./run.sh

# 方式2: Docker 运行（推荐）
docker run -d \
  --name runner-npu \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  -e RUNNER_REPO=https://github.com/computing-infra/pytorch-infra \
  -e RUNNER_TOKEN=<TOKEN> \
  -e RUNNER_LABELS=npu-910b \
  ghcr.io/computing-infra/ascend-ci/runner-npu:latest
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Runner 注册成功 | GitHub Actions → Runners 页面显示 Online |
| Runner Labels 正确 | 显示 `npu-910b` 标签 |
| Runner 可执行任务 | 手动触发简单 workflow，Runner 可以执行 |

**预计工时**: 1 天

---

#### Task 0.9.3: 配置 NPU 设备权限

**描述**: 配置 NPU 设备的访问权限，确保 Runner 进程可以访问

**工作内容**:
```bash
# 创建启动脚本
cat > /etc/rc.local << 'EOF'
chmod 666 /dev/davinci* 2>/dev/null || true
chmod 666 /dev/davinci_manager 2>/dev/null || true
chmod 666 /dev/devmm_svm 2>/dev/null || true
chmod 666 /dev/hisi_hdc 2>/dev/null || true
EOF

# 或配置 systemd 服务
```

**验证标准**:
| 验证项 | 验权方法 |
|--------|---------|
| 设备权限正确 | `ls -la /dev/davinci*` 显示 666 权限 |
| 非 root 可访问 | 非 root 用户可运行 `npu-smi info` |

**预计工时**: 0.5 天

---

## Phase 1: PR 集成验证

### 1.1 Smoke 测试设计

#### Task 1.1.1: 编写 Smoke 测试脚本

**描述**: 创建 `test/smoke_test.py` 快速验证脚本

**工作内容**:
```python
# test/smoke_test.py
def test_pytorch_import()
def test_torch_npu_import()
def test_npu_device()
def test_tensor_operations()
def test_nn_module()
def test_api_alignment()
def test_privateuse1_backend()
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 脚本存在 | `test/smoke_test.py` 文件存在 |
| CPU 环境可运行（部分测试） | `python test/smoke_test.py --cpu-only` 部分 PASS |
| NPU 环境全量 PASS | 在 NPU Runner 上全部 PASS |
| 执行时间 | < 5 分钟 |

**预计工时**: 1 天

---

#### Task 1.1.2: 创建 Smoke 测试 Workflow

**描述**: 创建 Smoke 测试独立 Workflow，作为 PR Gate 第一层

**工作内容**:
```yaml
# .github/workflows/smoke-test.yml
on:
  workflow_dispatch:
  repository_dispatch:
    types: [torch-npu-pr]

jobs:
  smoke-test:
    runs-on: [self-hosted, npu-910b]
    timeout-minutes: 20
    steps:
      - Checkout torch-npu
      - Setup NPU environment
      - Install PyTorch nightly
      - Build torch-npu
      - Run smoke_test.py
      - Report to PR (if triggered by PR)
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | `.github/workflows/smoke-test.yml` 存在 |
| 手动触发成功 | Actions 页面手动触发成功 |
| 测试全部 PASS | Step Summary 显示所有测试 PASS |
| PR Comment 报告 | PR 触发时，PR 页面有测试结果 Comment |

**预计工时**: 1 天

---

### 1.2 PR 触发机制

#### Task 1.2.1: 创建 PR Gate 主 Workflow

**描述**: 创建 `.github/workflows/pr-gate.yml` 作为 PR 门禁主入口

**工作内容**:
```yaml
# .github/workflows/pr-gate.yml
on:
  repository_dispatch:
    types: [torch-npu-pr]
  workflow_dispatch:
    inputs:
      torch_npu_repo, torch_npu_sha, pr_number

jobs:
  smoke-test:
    # 引用 smoke-test.yml 或内联
  device-agnostic-test:
    needs: smoke-test
    # Layer 2 测试
  npu-specific-test:
    needs: device-agnostic-test
    # Layer 3 测试
  aggregate-results:
    needs: [smoke-test, device-agnostic-test, npu-specific-test]
    # 汇总结果
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| Job 依赖正确 | smoke → device-agnostic → npu-specific 顺序执行 |
| 结果汇总正确 | aggregate-results 显示正确状态 |

**预计工时**: 1 天

---

#### Task 1.2.2: 配置 torch-npu 仓库触发（方案文档）

**描述**: 编写 torch-npu 仓库配置方案（实际配置需要 Ascend/pytorch 仓库权限）

**工作内容**:
```yaml
# 文档记录 torch-npu/.github/workflows/trigger-integration.yml
on:
  pull_request:
    branches: [master]

jobs:
  trigger:
    steps:
      - repository_dispatch to pytorch-infra
      - Comment on PR
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 配置方案完整 | 文档包含完整 YAML 配置 |
| 触发参数正确 | 包含 repo, sha, pr_number |

**预计工时**: 0.5 天

**备注**: 实际部署需要 Ascend/pytorch 仓库维护者配合

---

#### Task 1.2.3: 实现 PR Comment 反馈机制

**描述**: 在 Workflow 中实现 PR Comment 发布逻辑

**工作内容**:
```yaml
# 使用 actions/github-script@v7
- name: Report to PR
  if: inputs.pr_number != ''
  uses: actions/github-script@v7
  with:
    github-token: ${{ secrets.TORCH_NPU_TOKEN }}
    script: |
      github.rest.issues.createComment({
        owner, repo, issue_number, body
      });
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Token 配置 | `TORCH_NPU_TOKEN` Secret 存在 |
| Comment 格式正确 | Markdown 格式，包含测试结果表格 |
| Comment 发送成功 | 模拟 PR 触发，PR 页面有 Comment |

**预计工时**: 0.5 天

---

#### Task 1.2.4: 实现 GitHub Check 状态设置

**描述**: 设置 commit status 作为 PR 门禁状态

**工作内容**:
```yaml
- name: Set GitHub Check status
  uses: actions/github-script@v7
  script: |
    github.rest.repos.createCommitStatus({
      owner, repo, sha, state, context,
      description, target_url
    });
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Check 创建成功 | Commit 页面显示 `pytorch-infra/pr-gate` Check |
| 状态正确 | 成功时 green，失败时 red |
| 点击跳转 | 点击 Check 可跳转到 Workflow Run 页面 |

**预计工时**: 0.5 天

---

### 1.3 结果报告

#### Task 1.3.1: 设计测试报告模板

**描述**: 设计 PR Comment 的 Markdown 模板

**工作内容**:
```markdown
## 🔥 Smoke Test Results

**Status**: ✅ Passed

| Item | Value |
|------|-------|
| PyTorch nightly | `2.7.0.dev20250330` |
| torch-npu commit | `abc123` |
| Test duration | ~5 min |

✅ Basic integration verified.
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 模板文件存在 | `templates/pr_comment_template.md` 存在 |
| Markdown 渲染正确 | GitHub 上显示格式正确 |

**预计工时**: 0.5 天

---

#### Task 1.3.2: 实现结果汇总 Job

**描述**: 实现 aggregate-results job 汇总多层测试结果

**工作内容**:
```yaml
aggregate-results:
  needs: [smoke-test, device-agnostic-test, npu-specific-test]
  if: always()
  steps:
    - 判断各层结果
    - 设置最终状态
    - 发布最终 PR Comment
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 状态计算正确 | 根据各层结果正确判断最终状态 |
| Comment 包含所有层级 | 显示 Smoke/Device-Agnostic/NPU-Specific 三层结果 |

**预计工时**: 0.5 天

---

## Phase 2: 设备无关测试

### 2.1 测试分片配置

#### Task 2.1.1: 配置测试分片矩阵

**描述**: 在 Workflow 中配置 6 分片并行执行

**工作内容**:
```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4, 5, 6]
  fail-fast: false
env:
  SHARD_NUMBER: ${{ matrix.shard }}
  NUM_TEST_SHARDS: 6
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 6 个 Job 并行启动 | Workflow Run 显示 6 个并行 Job |
| 分片参数正确传递 | 每个 Job 的 SHARD_NUMBER 不同 |
| fail-fast: false | 一个分片失败不影响其他分片继续 |

**预计工时**: 0.5 天

---

#### Task 2.1.2: 实现分片测试选择逻辑

**描述**: 根据分片号选择不同的测试文件

**工作内容**:
```yaml
run: |
  case ${{ matrix.shard }} in
    1|2) TESTS="test_torch" ;;
    3|4) TESTS="test_ops" ;;
    5)   TESTS="test_nn" ;;
    6)   TESTS="test_autograd" ;;
  esac
  python test/run_test.py --include $TESTS --npu --shard ${{ matrix.shard }} 6
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 测试选择正确 | Shard 1-2 运行 test_torch 相关测试 |
| NPU 设备启用 | 测试在 NPU 上执行 |

**预计工时**: 0.5 天

---

### 2.2 PyTorch 测试集成

#### Task 2.2.1: 配置 PyTorch 测试下载

**描述**: 在 Workflow 中下载 PyTorch 测试套件

**工作内容**:
```yaml
- name: Download PyTorch test suite
  run: |
    git clone --depth=1 https://github.com/pytorch/pytorch.git /tmp/pytorch
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 克隆成功 | `/tmp/pytorch` 目录存在 |
| 测试文件存在 | `/tmp/pytorch/test/test_torch.py` 存在 |

**预计工时**: 0.5 天

---

#### Task 2.2.2: 配置 NPU 测试环境变量

**描述**: 设置 PyTorch 设备无关测试的 NPU 环境变量

**工作内容**:
```yaml
env:
  PYTORCH_TESTING_DEVICE_ONLY_FOR: npu
  PYTHONPATH: /tmp/pytorch
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 环境变量设置正确 | Job 中 env 显示正确值 |
| 仅运行 NPU 测试 | 测试输出显示 `Running tests for device: npu` |

**预计工时**: 0.5 天

---

### 2.3 测试结果处理

#### Task 2.3.1: 配置测试结果上传

**描述**: 配置测试结果 artifact 上传

**工作内容**:
```yaml
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: device-agnostic-shard-${{ matrix.shard }}
    path: /tmp/pytorch/test/test-reports/
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Artifact 上传成功 | Workflow Run 页面显示 6 个 Artifact |
| 结果文件存在 | Artifact 包含 XML/JSON 测试报告 |

**预计工时**: 0.5 天

---

## Phase 3: NPU 专用测试

### 3.1 torch-npu 测试集成

#### Task 3.1.1: 配置 torch-npu 专用测试运行

**描述**: 在 Workflow 中运行 torch-npu test 目录测试

**工作内容**:
```yaml
- name: Run NPU-specific tests
  run: |
    pytest test/ -v \
      --ignore=test/smoke/ \
      --ignore=test/distributed/ \
      -n auto \
      --tb=short
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| pytest 运行成功 | 测试输出显示 PASS/FAIL 统计 |
| 并行执行 | `-n auto` 自动使用多进程 |

**预计工时**: 0.5 天

---

### 3.2 每日定时测试

#### Task 3.2.1: 创建每日定时 Workflow

**描述**: 创建 `.github/workflows/nightly-integration.yml`

**工作内容**:
```yaml
on:
  schedule:
    - cron: '0 21 * * *'  # UTC 21:00 = 北京时间 05:00

jobs:
  get-latest-versions:
    # 获取 torch-npu 和 PyTorch 最新版本
  trigger-pr-gate:
    needs: get-latest-versions
    uses: ./.github/workflows/pr-gate.yml
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| 定时触发配置正确 | cron 表达式正确 |
| 版本获取成功 | get-latest-versions job 输出正确版本 |

**预计工时**: 0.5 天

---

### 3.3 Issue 追踪

#### Task 3.3.1: 创建 Issue 追踪 Workflow

**描述**: 创建 `.github/workflows/issue-tracker.yml`

**工作内容**:
```yaml
on:
  workflow_run:
    workflows: ["torch-npu-pr-gate"]
    types: [completed]

jobs:
  track-failure:
    if: workflow_run.conclusion == 'failure'
    # 创建兼容性 issue
  track-success:
    if: workflow_run.conclusion == 'success'
    # 关闭已修复 issue
```

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| Workflow 文件存在 | 文件在正确位置 |
| workflow_run 触发 | PR Gate 完成后自动触发 |
| Issue 创建逻辑 | 失败时检查是否创建 Issue |

**预计工时**: 1 天

---

## Phase 4: 扩展功能

### 4.1 分布式测试

#### Task 4.1.1: 申请多卡 NPU 资源

**描述**: 申请多卡 NPU Runner 用于分布式测试

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 多卡设备可用 | `npu-smi info` 显示多卡 |
| Runner Label 正确 | `npu-910b-4` 或类似标签 |

**预计工时**: 取决于审批

---

#### Task 4.1.2: 创建分布式测试 Workflow

**描述**: 创建 HCCL 分布式训练测试 Workflow

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 多卡测试运行成功 | 测试使用多卡执行 |
| HCCL 通信正常 | 分布式算子测试 PASS |

**预计工时**: 2 天

---

### 4.2 多架构支持

#### Task 4.2.1: 配置 910A/310P Runner

**描述**: 配置不同 NPU 架构的 Runner

**验证标准**:
| 验证项 | 验证方法 |
|--------|---------|
| 910A Runner 可用 | Label 包含 `npu-910a` |
| 310P Runner 可用 | Label 包含 `npu-310p` |

**预计工时**: 取决于资源

---

---

## 任务依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        任务依赖关系                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 0（基础设施）                                                          │
│  ───────────────                                                            │
│                                                                             │
│  0.1.1 ──→ 0.1.2 ──→ 0.1.3                                                  │
│  (命名空间)   (凭证)    (目录)                                                │
│                                                                             │
│  0.2.1 ──→ 0.2.2                                                            │
│  (Base      (Base                                                           │
│  Dockerfile) Workflow)                                                      │
│       │                                                                     │
│       ↓                                                                     │
│  0.3.1 ──→ 0.3.2                                                            │
│  (CANN      (CANN                                                           │
│  Dockerfile) Workflow)                                                      │
│       │                                                                     │
│       ↓                                                                     │
│  0.4.1 ──→ 0.4.2 ──→ 0.4.3                                                  │
│  (Runner    (entrypoint (Runner                                             │
│  Dockerfile)  script)   Workflow)                                           │
│       │                                                                     │
│       ↓                                                                     │
│  0.5.1 ──→ 0.5.2                                                            │
│  (Test      (Test                                                           │
│  Dockerfile) Workflow)                                                      │
│       │                                                                     │
│       ↓                                                                     │
│  0.6.1 ──→ 0.6.2                                                            │
│  (兼容矩阵    (兼容验证                                                        │
│   文件)      Workflow)                                                       │
│                                                                             │
│  0.7.1 (清理 Workflow)                                                      │
│                                                                             │
│  0.8.1 ──→ 0.8.2 ──→ 0.8.3    ← 关键阻塞点                                   │
│  (NPU资源)  (Runner安装) (设备权限)                                           │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────    │
│                              ↓ Phase 0 完成                                  │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  Phase 1（PR 集成验证）                                                       │
│  ─────────────────────                                                      │
│                                                                             │
│  1.1.1 ──→ 1.1.2                                                            │
│  (Smoke脚本) (Smoke Workflow)                                                │
│       │                                                                     │
│       ↓                                                                     │
│  1.2.1 ──→ 1.2.2 ──→ 1.2.3 ──→ 1.2.4                                        │
│  (PR Gate   (触发方案   (Comment   (GitHub                                    │
│   Workflow)   文档)     反馈)    Check)                                       │
│                                                                             │
│  1.3.1 ──→ 1.3.2                                                            │
│  (报告模板) (结果汇总)                                                         │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────    │
│                              ↓ Smoke 测试通过                                 │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  Phase 2（设备无关测试）                                                       │
│  ─────────────────────                                                      │
│                                                                             │
│  2.1.1 ──→ 2.1.2                                                            │
│  (分片矩阵) (分片选择)                                                         │
│                                                                             │
│  2.2.1 ──→ 2.2.2                                                            │
│  (PyTorch   (环境变量)                                                        │
│   测试下载)                                                                  │
│                                                                             │
│  2.3.1 (结果上传)                                                            │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────    │
│                              ↓ Phase 2 完成                                  │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  Phase 3（NPU 专用测试）                                                      │
│  ─────────────────────                                                      │
│                                                                             │
│  3.1.1 (torch-npu测试)                                                       │
│  3.2.1 (每日定时)                                                            │
│  3.3.1 (Issue追踪)                                                           │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────    │
│                              ↓ Phase 3 稳定                                  │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  Phase 4（扩展功能）                                                          │
│  ─────────────────────                                                      │
│                                                                             │
│  4.1.1 ──→ 4.1.2                                                            │
│  (多卡资源) (分布式测试)                                                       │
│                                                                             │
│  4.2.1 (多架构)                                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 任务清单汇总

| Phase | 任务数 | 预计工时 | 关键阻塞点 |
|-------|--------|---------|-----------|
| Phase 0 | 19 | 11 天 | NPU 资源申请 |
| Phase 1 | 12 | 5 天 | Phase 0 完成 |
| Phase 2 | 8 | 3 天 | Smoke 测试通过 |
| Phase 3 | 6 | 3 天 | Phase 2 完成 |
| Phase 4 | TBD | TBD | Phase 3 稳定 |
| **总计** | **45+** | **22+ 天** | |

---

## 验收标准

### Phase 0 验收

- [ ] Base Image 推送到 ghcr + swr
- [ ] CANN Image 推送到 swr
- [ ] Runner Image 推送到 ghcr + swr
- [ ] Test Image 推送到 ghcr + swr + quay
- [ ] NPU Runner 显示 Online 且可执行任务
- [ ] 兼容性验证 Workflow 成功运行一次

### Phase 1 验收

- [ ] Smoke 测试全部 PASS
- [ ] 手动触发 PR Gate Workflow 成功
- [ ] PR Comment 发布成功（模拟）
- [ ] GitHub Check 状态设置成功

### Phase 2 验收

- [ ] 6 分片并行执行成功
- [ ] Device-Agnostic 测试通过率 > 90%
- [ ] 测试结果 Artifact 正确上传

### Phase 3 验收

- [ ] torch-npu 专用测试 PASS
- [ ] 每日定时测试自动运行
- [ ] Issue 追踪机制运行

### Phase 4 验收

- [ ] 分布式测试运行成功
- [ ] 多架构测试支持

---

## 附录：关键决策点

| 决策点 | 选项 | 推荐 | 决策时机 |
|--------|------|------|---------|
| NPU 资源方案 | 自托管/CCI/ECS | 华为云 CCI | Phase 0 开始前 |
| Runner 运行方式 | 直接安装/Docker | Docker | Task 0.8.2 |
| 镜像存储策略 | 单仓库/多仓库 | 三仓库(ghcr+quay+swr) | Task 0.1.1 |
| CANN 版本 | 8.0.RC1/7.0.1 | 8.0.RC1 | Task 0.3.2 |
| 测试分片数 | 4/6/8 | 6 | Task 2.1.1 |