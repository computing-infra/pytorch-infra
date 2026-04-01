# ARM 版本 PyTorch NPU 测试执行方案

## 背景

阶段一（`nightly-build-arm.yml`）已完成 Ascend/pytorch 与 PyTorch nightly 的编译验证。阶段二需要执行 PyTorch 官方仓库的 NPU 覆盖核心功能测试。

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
│  5. 运行核心测试用例                                             │
│  6. 上传测试日志                                                 │
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

| 测试文件 | 用途 | 执行命令 |
|----------|------|----------|
| `test_torch.py` | 基础张量操作 | `python test/run_test.py --include test_torch --privateuseone` |
| `test_nn.py` | nn 模块测试 | `python test/run_test.py --include test_nn --privateuseone` |
| `test_autograd.py` | 自动微分 | `python test/run_test.py --include test_autograd --privateuseone` |
| `test_ops.py` | 算子测试 | `python test/run_test.py --include test_ops --privateuseone` |
| `test_transformers.py` | Transformer 模型 | `python test/run_test.py --include test_transformers --privateuseone` |

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

使用 `gh` 命令获取最近的构建产物：

```bash
RUN_ID=$(gh run list --repo computing-infra/pytorch-infra \
  --workflow=nightly-build-arm.yml \
  --status=success \
  --limit=1 \
  --json databaseId \
  -q '.[0].databaseId')

gh run download $RUN_ID --repo computing-infra/pytorch-infra \
  --pattern "torch_npu-wheel-arm-*" \
  --dir wheel_artifact
```

#### 3. 测试执行

```bash
# 设置 NPU 环境变量
export PYTORCH_TESTING_DEVICE_ONLY_FOR="privateuseone"

# 运行测试
python test/run_test.py \
  --include test_torch test_nn test_autograd test_ops \
  --privateuseone
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

（待更新）