# ARM 版本 PyTorch Nightly 构建验证方案

## 背景

原有的 `nightly-build.yml` 在 x86 平台（`ubuntu-22.04` runner）上验证 Ascend/pytorch 与 PyTorch nightly 的编译兼容性。为覆盖 ARM 平台（华为 NPU 环境），新增 ARM 版本构建 workflow。

## 方案设计

### 环境选型

| 项目 | x86 版本 | ARM 版本 |
|------|----------|----------|
| Runner | `ubuntu-22.04` | `[self-hosted, npu-910b]` |
| 运行方式 | 虚机直接运行 | Docker 容器 |
| Docker 镜像 | 无 | `swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331` |
| Python 版本 | 3.11（动态安装） | 3.11（镜像预装） |
| 预装 PyTorch | 无 | 2.11.0 a2（需验证兼容性） |

> **变更记录**：
> - 原计划使用 `manylinux2014` 镜像 → glibc 版本不兼容 Node.js 20
> - 尝试 `manylinux2_28` 镜像 → 网络超时无法访问 PyPI
> - 当前使用 `pytorch_2.11.0_a2_aarch64_builder` 镜像（华为云预构建）

### 构建流程

```
┌─────────────────────────────────────────────────────────────┐
│  npu-910b Runner + Docker Container                         │
├─────────────────────────────────────────────────────────────┤
│  1. Checkout 代码                                           │
│  2. 升级 torch 2.1.0 → nightly（pip3.11）                   │
│  3. Clone Ascend/pytorch（含子模块）                         │
│  4. Restore ccache                                          │
│  5. python3.11 setup.py build bdist_wheel                   │
│  6. Save ccache                                             │
│  7. 上传构建日志和 wheel                                     │
└─────────────────────────────────────────────────────────────┘
```

## 代码修改

### 新增文件

`.github/workflows/nightly-build-arm.yml`

### 关键配置差异

#### 1. Runner 和容器配置

```yaml
runs-on: npu-910b
container:
  image: quay.io/kerer/pytorch:arm-manylinux2014-nightly-20260326055807
  options: --user root
```

#### 2. Python 命令调整

镜像中 Python 路径为 `/opt/_internal/cpython-3.11.6/bin/python3.11`，已通过符号链接映射到 `python3.11`。

```bash
# 使用镜像预装的 Python 3.11
PYTHON=python3.11
PIP=pip3.11

$PIP install --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu
$PYTHON setup.py build bdist_wheel
```

#### 3. 移除的步骤

| 步骤 | 原因 |
|------|------|
| `setup-python` | 镜像已预装 Python 3.11 |
| `Install system dependencies` | manylinux 镜像已包含编译工具链 |

#### 4. 缓存 Key 前缀

添加 `arm` 前缀区分架构：

```yaml
key: ccache-arm-py3.11-${{ steps.clone_repo.outputs.commit }}
key: pip-arm-py3.11-torch-nightly
```

#### 5. Artifact 名称

添加 `-arm` 后缀：

```yaml
name: build-log-arm-${{ github.run_number }}
name: torch_npu-wheel-arm-${{ github.run_number }}
```

## 触发方式

与 x86 版本保持一致：

- **定时触发**：每日 UTC 22:00、03:00、08:00（北京时间 06:00、11:00、16:00）
- **手动触发**：`workflow_dispatch`，可选指定 PyTorch nightly 日期

## 后续工作

1. 推送 workflow 到远程仓库
2. 手动触发测试构建
3. 根据构建结果调整配置（如并行编译数、缓存大小等）
4. 如需长期维护，可考虑统一 x86/ARM workflow 使用矩阵构建

## 验证执行记录

### 2026-04-01 执行进展

#### ✅ 构建成功

| Run ID | 状态 | 结果 |
|--------|------|------|
| 23830621881 | ✅ 成功 | 构建耗时 23m18s，生成 wheel 包 |

**成功配置总结**：
- Runner: `[self-hosted, npu-910b]`
- 镜像: `swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/pytorch_2.11.0_a2_aarch64_builder:20260331`
- Python: 3.11
- 移除 auditwheel（aarch64 不可用）
- 构建产物: `torch_npu-wheel-arm-10`

### 缓存配置

**pip 缓存**：
```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-arm-py3.11-${{ hashFiles('**/requirements.txt') }}
```

**ccache 缓存**：
```yaml
- name: Cache ccache
  uses: actions/cache@v4
  with:
    path: ~/.cache/ccache
    key: ccache-arm-py3.11-${{ github.run_id }}
```

**ccache 使用说明**：
- 构建步骤自动检测 ccache 可用性
- 镜像无 ccache 时降级为无缓存编译
- ccache 最大缓存 10G

### PyTorch 版本说明

`2.11.0+cpu` 是正确的 ARM 版本：
- `+cpu` 后缀表示 CPU-only 版本（非 CUDA）
- PyTorch nightly 的 `cpu` 索引包含 aarch64 架构
- 构建出的 wheel 为 `manylinux_2_28_aarch64.whl`

---

#### 问题排查历程

#### 问题 1：Workflow 未触发

**现象**：推送代码后 workflow 未执行（0s 失败）

**原因**：self-hosted runner 使用 `runs-on` 必须包含 `self-hosted` 标签

**解决**：
```yaml
# 错误配置
runs-on: npu-910b

# 正确配置
runs-on: [self-hosted, npu-910b]
```

#### 问题 2：Docker 权限不足

**现象**：
```
permission denied while trying to connect to the Docker daemon socket
at unix:///var/run/docker.sock
```

**原因**：runner 用户 `ghrunner` 未加入 docker 组，或 runner 进程启动时未加载新组

**解决**：
```bash
# 添加用户到 docker 组
sudo usermod -aG docker ghrunner

# 重启 runner 进程（必须，否则进程不会加载新组）
cd /home/ghrunner/actions-runner
./run.sh
```

#### 问题 3：glibc 版本不兼容

**现象**：
```
/__e/node20/bin/node: /lib64/libc.so.6: version `GLIBC_2.28' not found
```

**原因**：manylinux2014 镜像 glibc 版本为 2.17，Node.js 20 需要 glibc 2.28+

**解决**：切换到 manylinux2_28 镜像

```yaml
# 原镜像（不兼容）
image: quay.io/kerer/pytorch:arm-manylinux2014-nightly-20260326055807

# 新镜像（兼容）
image: swr.cn-north-4.myhuaweicloud.com/frameworkptadapter/manylinux2_28_aarch64-builder:npu-20241231
```

#### 当前状态

| Run ID | 状态 | 失败原因 |
|--------|------|----------|
| 23830432863 | ❌ 失败 | auditwheel 在 aarch64 上无可用版本 |
| 23830194985 | ❌ 失败 | ccache 命令未找到（exit code 127） |
| 23829752650 | ❌ 失败 | 网络超时，无法连接 files.pythonhosted.org |
| 23829557682 | ❌ 失败 | glibc 版本不兼容（已解决） |
| 23828515786 | ❌ 失败 | Docker 权限不足（已解决） |

#### 问题 5：ccache 命令未找到

**现象**：
```
/__w/_temp/xxx.sh: line 4: ccache: command not found
Process completed with exit code 127
```

**原因**：镜像中未安装 ccache

**解决**：移除 ccache 和 pip cache 相关步骤，简化 workflow

#### 问题 6：auditwheel 在 aarch64 上不可用

**现象**：
```
ERROR: Could not find a version that satisfies the requirement auditwheel
ERROR: No matching distribution found for auditwheel
```

**原因**：auditwheel 仅支持 x86_64/i686 架构，不支持 aarch64

**解决**：移除 auditwheel 依赖

```yaml
# 仅安装 setuptools（auditwheel 在 ARM 上不可用）
$PIP install setuptools
```

**下一步**：等待构建完成验证流程

## 参考文件

- `.github/workflows/nightly-build.yml`（x86 版本）
- `.github/workflows/nightly-build-arm.yml`（ARM 版本）