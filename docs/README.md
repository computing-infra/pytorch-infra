# TTFHW-pytorch

PyTorch 异构硬件适配项目，专注于 Ascend NPU 等非 NVIDIA 硬件平台的 PyTorch 适配和优化。

## 文档目录

### CI/CD 镜像和门禁方案

| 文档 | 说明 |
|------|------|
| [01-pytorch-ci-image-gate-research.md](docs/01-pytorch-ci-image-gate-research.md) | PyTorch 各硬件设备 CI 镜像和门禁方案调研报告 |
| [02-ascend-npu-ci-image-gate-design.md](docs/02-ascend-npu-ci-image-gate-design.md) | Ascend NPU CI 镜像和门禁方案设计文档 |

## 项目结构

```
TTFHW-pytorch/
├── README.md
└── docs/
    ├── 01-pytorch-ci-image-gate-research.md      # 调研报告
    └── 02-ascend-npu-ci-image-gate-design.md     # NPU方案设计
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