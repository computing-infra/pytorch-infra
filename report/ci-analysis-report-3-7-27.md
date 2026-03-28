# CI 分析报告

本报告记录 kerer-ai/pytorch-npu 仓库 GitHub Actions 构建验证结果。

---

## 统计

- **总构建次数**: 25
- **成功次数**: 17
- **失败次数**: 8
- **成功率**: 68.0%
- **失败类型**: 克隆失败（4次）、编译失败（4次）

---

## 执行记录

| 执行时间 | 状态 | 构建时长 | 失败阶段 | Action 链接 |
|----------|------|----------|----------|-------------|
| 2026-03-28 04:19:40 UTC | ✅ 成功 | 63m14s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23677324552) |
| 2026-03-27 04:32:20 UTC | ✅ 成功 | 63m43s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23631280527) |
| 2026-03-26 05:55:51 UTC | ❌ 失败 | 57m31s | Build torch_npu wheel | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23579809499) |
| 2026-03-26 04:31:09 UTC | ❌ 失败 | 55m35s | Build torch_npu wheel | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23577598557) |
| 2026-03-25 04:19:53 UTC | ✅ 成功 | 62m25s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23524724631) |
| 2026-03-24 04:17:28 UTC | ✅ 成功 | 63m31s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23472856579) |
| 2026-03-23 04:27:07 UTC | ✅ 成功 | 63m5s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23421450775) |
| 2026-03-22 04:19:09 UTC | ❌ 失败 | 1m23s | Clone Ascend/pytorch | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23395523059) |
| 2026-03-21 04:03:34 UTC | ❌ 失败 | 1m18s | Clone Ascend/pytorch | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23371610314) |
| 2026-03-20 04:12:30 UTC | ❌ 失败 | 1m26s | Clone Ascend/pytorch | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23328742960) |
| 2026-03-19 04:21:54 UTC | ✅ 成功 | 60m17s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23279690053) |
| 2026-03-18 04:23:31 UTC | ✅ 成功 | 63m43s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23228997240) |
| 2026-03-17 04:17:08 UTC | ✅ 成功 | 61m47s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23178176374) |
| 2026-03-16 04:38:40 UTC | ❌ 失败 | 3m45s | Clone Ascend/pytorch | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23128194179) |
| 2026-03-15 04:31:13 UTC | ✅ 成功 | 61m52s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23103368696) |
| 2026-03-14 04:08:54 UTC | ✅ 成功 | 63m3s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23080079008) |
| 2026-03-13 04:10:48 UTC | ✅ 成功 | 62m59s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23035810284) |
| 2026-03-12 04:12:20 UTC | ✅ 成功 | 62m18s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22986250078) |
| 2026-03-11 04:08:13 UTC | ✅ 成功 | 60m38s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22936265347) |
| 2026-03-10 04:07:47 UTC | ✅ 成功 | 63m41s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22886639530) |
| 2026-03-09 04:15:49 UTC | ✅ 成功 | 61m18s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22838115797) |
| 2026-03-08 04:09:55 UTC | ✅ 成功 | 60m54s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22813596807) |
| 2026-03-07 15:36:22 UTC | ✅ 成功 | 63m11s | - | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22801901830) |
| 2026-03-07 14:31:31 UTC | ❌ 失败 | 56m41s | Build torch_npu wheel | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800875730) |
| 2026-03-07 13:59:39 UTC | ❌ 失败 | 10m19s | Build torch_npu wheel | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800386680) |

---

## 失败分析

### 克隆失败（4次）

发生在 `Clone Ascend/pytorch (with submodules)` 步骤，构建时长极短（1-4分钟），表明克隆阶段即失败。

| 日期 | Run ID | 可能原因 |
|------|--------|----------|
| 2026-03-22 | 23395523059 | 网络问题/仓库访问问题 |
| 2026-03-21 | 23371610314 | 网络问题/仓库访问问题 |
| 2026-03-20 | 23328742960 | 网络问题/仓库访问问题 |
| 2026-03-16 | 23128194179 | 网络问题/仓库访问问题 |

### 编译失败（4次）

发生在 `Build torch_npu wheel` 步骤，构建时长较长（55-57分钟），表明编译过程中出错。

| 日期 | Run ID | 失败阶段 | Artifact |
|------|--------|----------|----------|
| 2026-03-26 | 23579809499 | Build torch_npu wheel | build-log-23 |
| 2026-03-26 | 23577598557 | Build torch_npu wheel | build-log-22 |
| 2026-03-07 | 22800875730 | Build torch_npu wheel | build-log-2 |
| 2026-03-07 | 22800386680 | Build torch_npu wheel | build-log-1 |

**说明**：详细编译错误信息需下载对应 artifact 中的 `build-log-*` 文件查看。

---

> 报告更新时间: 2026-03-28
> 数据来源: https://github.com/kerer-ai/pytorch-npu/actions