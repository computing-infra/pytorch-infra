# torch-npu ↔ PyTorch 集成验证方案

通过中间 CI 仓库实现 torch-npu 与 PyTorch 的集成验证，提供类似 NVIDIA CUDA、AMD ROCm、Intel XPU 在 PyTorch 主仓的门禁体验。

## 文档目录

| 文档 | 说明 |
|------|------|
| [01-pytorch-ci-image-gate-research.md](docs/01-pytorch-ci-image-gate-research.md) | PyTorch 各硬件设备 CI 镜像和门禁方案调研报告 |
| [02-ascend-npu-ci-image-gate-design.md](docs/02-ascend-npu-ci-image-gate-design.md) | torch-npu ↔ PyTorch 集成验证方案设计文档 |
| [03-ascend-npu-ci-development-plan.md](docs/03-ascend-npu-ci-development-plan.md) | 开发计划和任务拆解，每个子任务可独立验证 |

## 设计文档章节概览

### 02-ascend-npu-ci-image-gate-design.md

| 章节 | 核心内容 |
|------|---------|
| **一、项目定位与目标** | 中间 CI 仓库定位、核心目标、与其他设备对比 |
| **二、镜像体系设计** | 四层镜像架构、构建策略、CANN兼容矩阵、Dockerfile设计、多仓库管理 |
| **三、镜像构建 Workflow** | Base/CANN/Runner/Test Image构建、兼容性验证、镜像清理 |
| **四、第一阶段方案设计** | PR 集成验证目标、PrivateUse1 Backend 机制、集成验证流程、测试分层策略 |
| **五、Workflow 设计** | pr-gate.yml、torch-npu 触发配置、每日定时测试 |
| **六、Issue 追踪机制** | 兼容性问题自动追踪 |
| **七、Runner 环境配置** | Runner 类型、环境准备、华为云 CCI 方案 |
| **八、实施路线图** | Phase 1-4 详细任务清单和验收标准 |
| **九、附录** | 环境变量、版本获取、常见问题处理 |

### 03-ascend-npu-ci-development-plan.md

| 章节 | 核心内容 |
|------|---------|
| **开发阶段概览** | Phase 0-4 总览、任务数统计、阻塞点识别 |
| **Phase 0: 基础设施** | 镜像体系(7任务)、各层镜像构建(6任务)、Runner环境(3任务) |
| **Phase 1: PR 集成验证** | Smoke测试(2任务)、PR触发机制(4任务)、结果报告(2任务) |
| **Phase 2: 设备无关测试** | 测试分片(2任务)、PyTorch测试集成(2任务)、结果处理(1任务) |
| **Phase 3: NPU 专用测试** | torch-npu测试、每日定时、Issue追踪 |
| **Phase 4: 扩展功能** | 分布式测试、多架构支持 |
| **任务依赖关系图** | 可视化任务依赖链路 |
| **验收标准** | 各 Phase 完成验收条件 |

## 核心架构

```
torch-npu (Ascend/pytorch)  →  pytorch-infra (中间CI)  →  PyTorch nightly
        ↓                              ↓                       ↓
   PR 提交              触发集成测试              提供基础镜像
        ↓                              ↓                       ↓
   自动验证              运行 NPU 测试             设备无关测试
        ↓                              ↓                       ↓
   PR Comment           结果反馈                  兼容性报告
```

## 第一阶段目标

让 torch-npu 的 PR 或最新代码能够及时与 PyTorch 集成测试：

- **触发延迟**: < 1 分钟
- **Smoke 测试**: < 15 分钟
- **完整测试**: < 60 分钟
- **反馈方式**: PR Comment + GitHub Check

## 项目结构

```
pytorch-infra/
├── .github/
│   └── workflows/           # CI Workflow（待开发）
├── dockerfiles/             # 镜像 Dockerfile（待开发）
│   ├── base-npu/
│   ├── cann-npu/
│   ├── runner-npu/
│   └── test-npu/
├── test/                    # 测试脚本（待开发）
│   └── smoke_test.py
├── docs/
│   ├── README.md            # 文档索引
│   ├── 01-pytorch-ci-image-gate-research.md      # 调研报告
│   ├── 02-ascend-npu-ci-image-gate-design.md     # NPU方案设计
│   └── 03-ascend-npu-ci-development-plan.md      # 开发计划和任务拆解
└── compatibility_matrix.json # 版本兼容矩阵（待开发）
```

## 调研范围

本项目的调研报告覆盖以下硬件平台的 CI 镜像和门禁方案：

- **NVIDIA CUDA** - 主流GPU平台，包括 H100/B200 等
- **AMD ROCm** - AMD GPU 平台，包括 MI200/MI300/MI355 等
- **Intel XPU** - Intel GPU 平台，包括 PVC/Arc 等
- **ARM aarch64** - ARM64 架构 CPU
- **IBM s390x** - IBM 大型机架构
- **RISC-V** - RISC-V 架构（交叉编译）
- **Apple macOS** - Apple Silicon 平台

## 方案特点

NPU CI 方案设计借鉴了以下成熟方案：

1. **ROCm 方案**
   - 多架构支持 (gfx90a/gfx942/gfx950)
   - 高频回归测试
   - 分布式测试支持

2. **XPU 方案**
   - Driver 类型区分 (LTS/CLIENT)
   - oneAPI 集成模式
   - Smoke 测试设计

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。