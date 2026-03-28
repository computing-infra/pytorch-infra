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

## Open Issues

当前无 open issue。

### 已关闭 Issues

| Issue | 标题 | 状态 |
|-------|------|------|
| [#1](https://github.com/computing-infra/pytorch-infra/issues/1) | ProcessGroupHCCL.cpp 使用不存在的 SocVersion::Ascend910_95 枚举值 | ✅ 已修复 |
| [#12](https://github.com/computing-infra/pytorch-infra/issues/12) | CachingHostAllocator 接口重构 | ✅ 已修复 |
| [#13](https://github.com/computing-infra/pytorch-infra/issues/13) | SymmetricMemory 接口演进 | ✅ 已修复 |

---

## 执行记录

| 执行时间 | 状态 | PyTorch Nightly | Ascend/pytorch Commit | 构建时长 | Action 链接 | 发现问题 | Issue |
|----------|------|-----------------|----------------------|----------|-------------|----------|-------|
| 2026-03-28 04:19:40 UTC | ✅ 成功 | 2.12.0.dev20260327+cpu | - | 63m14s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23677324552) | 无 | |
| 2026-03-27 04:32:20 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | - | 63m43s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23631280527) | 无 | |
| 2026-03-26 05:55:51 UTC | ❌ 失败 | 2.12.0.dev20260325+cpu | - | 57m31s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23579809499) | **编译失败**: `Ascend910_95` not member of `SocVersion` (`ProcessGroupHCCL.cpp:430`) | [#1](https://github.com/computing-infra/pytorch-infra/issues/1) |
| 2026-03-26 04:31:09 UTC | ❌ 失败 | 2.12.0.dev20260325+cpu | - | 55m35s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23577598557) | **编译失败**: `Ascend910_95` not member of `SocVersion` (`ProcessGroupHCCL.cpp:430`) | [#1](https://github.com/computing-infra/pytorch-infra/issues/1) |
| 2026-03-25 04:19:53 UTC | ✅ 成功 | 2.12.0.dev20260324+cpu | - | 62m25s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23524724631) | 无 | |
| 2026-03-24 04:17:28 UTC | ✅ 成功 | 2.12.0.dev20260323+cpu | - | 63m31s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23472856579) | 无 | |
| 2026-03-23 04:27:07 UTC | ✅ 成功 | 2.12.0.dev20260322+cpu | - | 63m5s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23421450775) | 无 | |
| 2026-03-22 04:19:09 UTC | ❌ 失败 | - | - | 1m23s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23395523059) | **克隆失败**: Ascend/pytorch 仓库克隆超时（网络问题） | |
| 2026-03-21 04:03:34 UTC | ❌ 失败 | - | - | 1m18s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23371610314) | **克隆失败**: Ascend/pytorch 仓库克隆超时（网络问题） | |
| 2026-03-20 04:12:30 UTC | ❌ 失败 | - | - | 1m26s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23328742960) | **克隆失败**: Ascend/pytorch 仓库克隆超时（网络问题） | |
| 2026-03-19 04:21:54 UTC | ✅ 成功 | 2.12.0.dev20260318+cpu | - | 60m17s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23279690053) | 无 | |
| 2026-03-18 04:23:31 UTC | ✅ 成功 | 2.12.0.dev20260317+cpu | - | 63m43s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23228997240) | 无 | |
| 2026-03-17 04:17:08 UTC | ✅ 成功 | 2.12.0.dev20260316+cpu | - | 61m47s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23178176374) | 无 | |
| 2026-03-16 04:38:40 UTC | ❌ 失败 | - | - | 3m45s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23128194179) | **克隆失败**: Ascend/pytorch 仓库克隆超时（网络问题） | |
| 2026-03-15 04:31:13 UTC | ✅ 成功 | 2.12.0.dev20260314+cpu | - | 61m52s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23103368696) | 无 | |
| 2026-03-14 04:08:54 UTC | ✅ 成功 | 2.12.0.dev20260313+cpu | - | 63m3s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23080079008) | 无 | |
| 2026-03-13 04:10:48 UTC | ✅ 成功 | 2.12.0.dev20260312+cpu | - | 62m59s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/23035810284) | 无 | |
| 2026-03-12 04:12:20 UTC | ✅ 成功 | 2.12.0.dev20260311+cpu | - | 62m18s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22986250078) | 无 | |
| 2026-03-11 04:08:13 UTC | ✅ 成功 | 2.12.0.dev20260310+cpu | - | 60m38s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22936265347) | 无 | |
| 2026-03-10 04:07:47 UTC | ✅ 成功 | 2.12.0.dev20260309+cpu | - | 63m41s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22886639530) | 无 | |
| 2026-03-09 04:15:49 UTC | ✅ 成功 | 2.12.0.dev20260308+cpu | - | 61m18s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22838115797) | 无 | |
| 2026-03-08 04:09:55 UTC | ✅ 成功 | 2.12.0.dev20260307+cpu | - | 60m54s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22813596807) | 无 | |
| 2026-03-07 15:36:22 UTC | ✅ 成功 | 2.12.0.dev20260306+cpu | - | 63m11s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22801901830) | 无 | |
| 2026-03-07 14:31:31 UTC | ❌ 失败 | 2.12.0.dev20260306+cpu | - | 56m41s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800875730) | **编译失败**: `GroupInfo` has no member `rank_to_global_rank` (`NPUSHMEMSymmetricMemory.cpp`) | [#13](https://github.com/computing-infra/pytorch-infra/issues/13) |
| 2026-03-07 13:59:39 UTC | ❌ 失败 | 2.12.0.dev20260306+cpu | - | 10m19s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800386680) | **编译失败**: `CachingHostAllocator` API 重构 (`blocks`→`blocks_`, `process_events` 签名变更) | [#12](https://github.com/computing-infra/pytorch-infra/issues/12) |

---

## 失败分析

### 克隆失败（4次）

发生在 `Clone Ascend/pytorch (with submodules)` 步骤，构建时长极短（1-4分钟），表明克隆阶段即失败。属于网络问题，非代码兼容性问题。

| 日期 | Run ID | 可能原因 |
|------|--------|----------|
| 2026-03-22 | 23395523059 | 网络问题/仓库访问问题 |
| 2026-03-21 | 23371610314 | 网络问题/仓库访问问题 |
| 2026-03-20 | 23328742960 | 网络问题/仓库访问问题 |
| 2026-03-16 | 23128194179 | 网络问题/仓库访问问题 |

### 编译失败（4次）

发生在 `Build torch_npu wheel` 步骤，构建时长较长（55-57分钟），表明编译过程中出错。

| 日期 | Run ID | 错误类型 | 相关 Issue |
|------|--------|----------|------------|
| 2026-03-26 | 23579809499 | `Ascend910_95` 枚举不存在 | [#1](https://github.com/computing-infra/pytorch-infra/issues/1) |
| 2026-03-26 | 23577598557 | `Ascend910_95` 枚举不存在 | [#1](https://github.com/computing-infra/pytorch-infra/issues/1) |
| 2026-03-07 | 22800875730 | `GroupInfo.rank_to_global_rank` 成员不存在 | [#13](https://github.com/computing-infra/pytorch-infra/issues/13) |
| 2026-03-07 | 22800386680 | `CachingHostAllocator` API 重构 | [#12](https://github.com/computing-infra/pytorch-infra/issues/12) |

**说明**：`Ascend/pytorch Commit` 列因日志已过期无法获取，标记为 `-`。详细编译错误信息可从 artifact 中 `build-log-*` 文件查看。

---

> 报告更新时间: 2026-03-28
> 数据来源: https://github.com/kerer-ai/pytorch-npu/actions