# NPU Build and Test 一体化方案

## 背景

现有的 NPU 测试方案采用两阶段分离架构：
1. **阶段一** (`nightly-build-arm.yml`)：构建 torch_npu wheel
2. **阶段二** (`npu-test.yml`)：下载 wheel 并执行测试

本次方案将这两个阶段合并为一个 workflow，实现"构建 → 安装 → 测试"的一体化流程。

## 方案设计

### 架构对比

| 架构 | 流程 | 优点 | 缺点 |
|------|------|------|------|
| 分离架构 | Build → artifact → Download → Test | wheel 可复用，测试可独立重试 | 依赖 artifact 传递，增加复杂度 |
| 一体化架构 | Build → Install → Test（同 workflow） | 流程简单，无需 artifact 传递 | 构建失败时无法单独重试测试 |

### 修改文件

`.github/workflows/npu-test.yml`

### 流程变更

```
┌─────────────────────────────────────────────────────────────────┐
│  npu-910b Runner + Docker Container（挂载 NPU 卡）              │
├─────────────────────────────────────────────────────────────────┤
│  原流程：                                                        │
│  1. Checkout pytorch-infra                                       │
│  2. Download wheel artifact（从 nightly-build-arm.yml）          │
│  3. Install torch nightly + torch_npu wheel                     │
│  4. Clone 官方 pytorch 仓库                                      │
│  5. 运行 PyTorch 官方测试                                        │
├─────────────────────────────────────────────────────────────────┤
│  新流程：                                                        │
│  1. Checkout pytorch-infra                                       │
│  2. Uninstall pre-installed torch/torchvision                   │
│  3. Install PyTorch nightly                                      │
│  4. Clone Ascend/pytorch 源码                                    │
│  5. Build torch_npu wheel (ci/build.sh)                         │
│  6. Install torch_npu wheel                                      │
│  7. Load CANN environment                                        │
│  8. Run test/npu/test_device.py                                  │
│  9. Upload build/test logs                                       │
│  10. Upload wheel artifact                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Steps 详细设计

#### 1. Checkout

保持现有配置：
```yaml
- name: Checkout pytorch-infra (via proxy)
  shell: bash
  run: |
    rm -rf * .[!.]* 2>/dev/null || true
    git clone --depth=1 https://gh-proxy.test.osinfra.cn/https://github.com/computing-infra/pytorch-infra.git .
```

#### 2. Setup cache directories

```yaml
- name: Setup cache directories
  run: |
    mkdir -p ~/.cache/pip
    mkdir -p ~/.cache/ccache
    chmod -R 777 ~/.cache
```

#### 3. Cache pip

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-arm-py${{ env.PYTHON_VERSION }}-build-test
    restore-keys: |
      pip-arm-py${{ env.PYTHON_VERSION }}-
```

#### 4. Cache ccache

```yaml
- name: Cache ccache
  uses: actions/cache@v4
  with:
    path: ~/.cache/ccache
    key: ccache-arm-py${{ env.PYTHON_VERSION }}-${{ github.run_id }}
    restore-keys: |
      ccache-arm-py${{ env.PYTHON_VERSION }}-
```

#### 5. Uninstall pre-installed torch

```yaml
- name: Uninstall pre-installed torch/torchvision
  run: |
    pip${{ env.PYTHON_VERSION }} uninstall -y torch torchvision || true
    echo "Pre-installed torch/torchvision uninstalled"
```

#### 6. Install PyTorch nightly

```yaml
- name: Install PyTorch nightly
  id: install_torch
  run: |
    PIP=pip${{ env.PYTHON_VERSION }}
    PYTHON=python${{ env.PYTHON_VERSION }}

    export PIP_CACHE_DIR=~/.cache/pip
    $PIP install --upgrade pip

    # 安装 PyTorch nightly（CPU 版，aarch64）
    $PIP install --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu

    TORCH_VER=$($PYTHON -c "import torch; print(torch.__version__)")
    echo "version=${TORCH_VER}" >> $GITHUB_OUTPUT
    echo "PyTorch nightly version: ${TORCH_VER}"
```

#### 7. Clone Ascend/pytorch

```yaml
- name: Clone Ascend/pytorch
  id: clone_repo
  run: |
    git clone --depth=1 --recurse-submodules \
      https://gitcode.com/Ascend/pytorch.git ascend_pytorch
    cd ascend_pytorch
    COMMIT=$(git rev-parse HEAD)
    COMMIT_SHORT=$(git rev-parse --short HEAD)
    COMMIT_DATE=$(git log -1 --format='%ci')
    echo "commit=${COMMIT}" >> $GITHUB_OUTPUT
    echo "commit_short=${COMMIT_SHORT}" >> $GITHUB_OUTPUT
    echo "commit_date=${COMMIT_DATE}" >> $GITHUB_OUTPUT
    echo "Ascend/pytorch commit: ${COMMIT} (${COMMIT_DATE})"
```

#### 8. Build torch_npu wheel

使用 `ci/build.sh` 脚本：

```yaml
- name: Build torch_npu wheel
  id: build
  run: |
    PYTHON=python${{ env.PYTHON_VERSION }}
    cd ascend_pytorch

    # 配置 ccache
    if command -v ccache &> /dev/null; then
      ccache -M 10G
      ccache -z || true
      export CC="ccache gcc"
      export CXX="ccache g++"
      export CCACHE_DIR=~/.cache/ccache
      export CCACHE_COMPRESS=1
      export CCACHE_MAXSIZE=10G
      export CCACHE_BASEDIR="${PWD}"
      USE_CCACHE=1
    fi

    # 构建参数
    export MAX_JOBS=$(nproc)
    export DISABLE_INSTALL_TORCHAIR=FALSE
    export BUILD_WITHOUT_SHA=1

    # 使用 ci/build.sh 脚本
    bash ci/build.sh --python=${{ env.PYTHON_VERSION }} 2>&1 | tee /tmp/build.log
    BUILD_STATUS=${PIPESTATUS[0]}

    # ccache 统计
    if [ "${USE_CCACHE}" = "1" ]; then
      ccache -s
    fi

    echo "status=${BUILD_STATUS}" >> $GITHUB_OUTPUT
    if [ ${BUILD_STATUS} -eq 0 ]; then
      WHL=$(ls dist/*.whl 2>/dev/null | head -1)
      echo "wheel=${WHL}" >> $GITHUB_OUTPUT
      echo "Build succeeded: ${WHL}"
    fi
    exit ${BUILD_STATUS}
```

**ci/build.sh 脚本说明**：
- 参数：`--python=3.11` 指定 Python 版本
- 内部执行：`python${PY_VERSION} setup.py build bdist_wheel`
- 其他可选参数：`--disable_torchair`, `--disable_rpc`, `--enable_lto`

#### 9. Install torch_npu wheel

```yaml
- name: Install torch_npu wheel
  run: |
    pip${{ env.PYTHON_VERSION }} install ascend_pytorch/dist/torch_npu*.whl
    echo "torch_npu wheel installed"
```

#### 10. Load CANN environment

```yaml
- name: Load CANN environment
  shell: bash
  run: |
    source /usr/local/Ascend/cann/set_env.sh 2>/dev/null || true
    source /usr/local/Ascend/nnal/atb/set_env.sh 2>/dev/null || true

    # 手动设置关键环境变量（确保路径正确）
    export CANN_PATH=/usr/local/Ascend/cann
    export LD_LIBRARY_PATH=$CANN_PATH/lib64:$CANN_PATH/lib64/plugin/opskernel:$CANN_PATH/lib64/plugin/nnengine:$CANN_PATH/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64:$CANN_PATH/tools/aml/lib64:$CANN_PATH/tools/aml/lib64/plugin:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/nnal/atb/latest/atb/cxx_abi_1/lib:$LD_LIBRARY_PATH
    export ASCEND_HOME_PATH=$CANN_PATH
    export ASCEND_OPP_PATH=$CANN_PATH/opp

    echo "CANN environment loaded"
    echo "ASCEND_HOME_PATH: $ASCEND_HOME_PATH"
```

#### 11. Verify NPU availability

```yaml
- name: Verify NPU availability
  shell: bash
  run: |
    source /usr/local/Ascend/cann/set_env.sh 2>/dev/null || true
    source /usr/local/Ascend/nnal/atb/set_env.sh 2>/dev/null || true

    export CANN_PATH=/usr/local/Ascend/cann
    export ASCEND_HOME_PATH=$CANN_PATH
    export ASCEND_OPP_PATH=$CANN_PATH/opp
    export LD_LIBRARY_PATH=$CANN_PATH/lib64:...

    python${{ env.PYTHON_VERSION }} -c "import torch; import torch_npu; print(f'torch: {torch.__version__}'); print(f'torch_npu: {torch_npu.__version__}'); print(f'NPU available: {torch.npu.is_available()}'); print(f'NPU count: {torch.npu.device_count()}')"
```

#### 12. Run test_device.py

```yaml
- name: Run test_device.py
  id: run_tests
  shell: bash
  run: |
    source /usr/local/Ascend/cann/set_env.sh 2>/dev/null || true
    source /usr/local/Ascend/nnal/atb/set_env.sh 2>/dev/null || true

    export CANN_PATH=/usr/local/Ascend/cann
    export ASCEND_HOME_PATH=$CANN_PATH
    export ASCEND_OPP_PATH=$CANN_PATH/opp
    export LD_LIBRARY_PATH=$CANN_PATH/lib64:...

    pip${{ env.PYTHON_VERSION }} install pytest pytest-xdist

    cd ascend_pytorch/test
    python${{ env.PYTHON_VERSION }} -m pytest npu/test_device.py -v 2>&1 | tee /tmp/test.log

    if [ $? -eq 0 ]; then
      echo "status=0" >> $GITHUB_OUTPUT
      echo "test_device.py: PASSED"
    else
      echo "status=1" >> $GITHUB_OUTPUT
      echo "test_device.py: FAILED"
    fi
```

**测试文件位置**：
- Ascend/pytorch 测试目录：`test/`
- NPU 设备测试：`test/npu/test_device.py`
- 其他可用测试：`test/npu/*.py`, `test/test_npu.py`

#### 13. Upload logs

```yaml
- name: Upload build log
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: build-log-${{ github.run_number }}
    path: /tmp/build.log
    if-no-files-found: warn

- name: Upload test log
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-log-${{ github.run_number }}
    path: /tmp/test.log
    if-no-files-found: warn
```

#### 14. Upload wheel artifact

```yaml
- name: Upload wheel artifact
  if: steps.build.outputs.status == '0'
  uses: actions/upload-artifact@v4
  with:
    name: torch_npu-wheel-${{ github.run_number }}
    path: ascend_pytorch/dist/*.whl
    if-no-files-found: warn
```

#### 15. Summary

```yaml
- name: Build and Test summary
  if: always()
  run: |
    BUILD_STATUS="${{ steps.build.outputs.status }}"
    TEST_STATUS="${{ steps.run_tests.outputs.status }}"

    if [ "${BUILD_STATUS}" = "0" ]; then
      BUILD_ICON="✅ SUCCESS"
    else
      BUILD_ICON="❌ FAILED"
    fi

    if [ "${TEST_STATUS}" = "0" ]; then
      TEST_ICON="✅ PASSED"
    else
      TEST_ICON="❌ FAILED"
    fi

    cat >> $GITHUB_STEP_SUMMARY << EOF
    ## NPU Build and Test

    | 项目 | 详情 |
    |------|------|
    | 执行时间 | $(date -u '+%Y-%m-%d %H:%M UTC') |
    | Docker 镜像 | \`${{ env.DOCKER_IMAGE }}\` |
    | PyTorch Nightly | \`${{ steps.install_torch.outputs.version }}\` |
    | Ascend/pytorch Commit | [\`${{ steps.clone_repo.outputs.commit_short }}\`](https://gitcode.com/Ascend/pytorch/commit/${{ steps.clone_repo.outputs.commit }}) |
    | Commit 时间 | ${{ steps.clone_repo.outputs.commit_date }} |
    | 构建结果 | ${BUILD_ICON} |
    | 测试结果 | ${TEST_ICON} |

    $( [ "${BUILD_STATUS}" = "0" ] && echo "> Wheel: \`${{ steps.build.outputs.wheel }}\`" || echo "> 查看 build-log artifact 获取详细错误信息" )
    EOF
```

### 容器配置

保持现有配置，参考 `docs/npu-test-plan.md` 的验证记录：

```yaml
container:
  image: swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331
  options: --user root --device /dev/davinci4 --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi -v /usr/local/Ascend/driver:/usr/local/Ascend/driver -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware -v /usr/local/Ascend/cann:/usr/local/Ascend/cann -v /usr/local/Ascend/nnal:/usr/local/Ascend/nnal
```

### 环境变量

```yaml
env:
  PYTHON_VERSION: '3.11'
  DOCKER_IMAGE: swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331
  AUDITWHEEL_PLAT: 'skip'  # 跳过 auditwheel repair
```

### 触发方式

保持现有配置：

```yaml
on:
  push:
    paths:
      - '.github/workflows/npu-test.yml'
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00（北京时间次日 07:00）
  workflow_dispatch:
```

## 关键差异点

### 与现有 npu-test.yml 的差异

| 项目 | 现有 | 新方案 |
|------|------|--------|
| wheel 来源 | 下载 artifact | 本地构建 |
| PyTorch 源码 | 官方 pytorch | Ascend/pytorch |
| 测试来源 | PyTorch 官方 tests | Ascend/pytorch tests |
| 测试文件 | test_torch, test_nn 等 | test/npu/test_device.py |

### ci/build.sh vs setup.py

| 方式 | 命令 | 说明 |
|------|------|------|
| ci/build.sh | `bash ci/build.sh --python=3.11` | 提供参数解析，内部调用 setup.py |
| setup.py | `python3.11 setup.py build bdist_wheel` | 直接构建 |

推荐使用 `ci/build.sh`，因为它：
- 提供了 Python 版本参数化
- 统一了构建入口
- 支持 `--disable_torchair` 等可选参数

## Verification

修改完成后验证步骤：
1. Push workflow 文件触发 CI 运行
2. 检查构建日志确认 wheel 生成成功
3. 检查测试日志确认 test_device.py 执行成功
4. 查看 Summary 输出的关键信息（PyTorch 版本、Commit、结果）
5. 确认 wheel artifact 上传成功

---

## 相关文档

- [NPU 测试执行方案](./npu-test-plan.md) - 原两阶段方案和测试框架分析
- [ARM 版本构建方案](./arm-nightly-build-plan.md) - ARM 构建配置参考