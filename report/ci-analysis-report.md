# CI 分析报告

本报告记录 Ascend/pytorch 与 PyTorch Nightly 的每日集成验证结果。

---

## 执行记录

| 执行时间 | 状态 | PyTorch Nightly | Ascend/pytorch Commit | 构建时长 | Action 链接 | 发现问题 |
|----------|------|-----------------|----------------------|----------|-------------|----------|
| 2026-03-28 04:52:35 UTC | ✅ 成功 | 2.12.0.dev20260327+cpu | `cebf05bc` | 7m7s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23677856986) | 无 |
| 2026-03-27 22:23:34 UTC | ✅ 成功 | 2.12.0.dev20260327+cpu | `f0c9bfe4` | 1h13m | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23670028060) | 无 |
| 2026-03-27 08:59:52 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `e787d68d` | 7m20s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23638769452) | 无 |
| 2026-03-27 05:07:03 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `6c59120e` | 7m50s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23632119373) | 无 |
| 2026-03-27 01:36:32 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `91a4eb79` | 6m48s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23626806955) | 无 |
| 2026-03-26 22:20:03 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `e787d68d` | 1h6m | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23620863183) | 无 |
| 2026-03-26 12:53:45 UTC | ❌ 失败 | 2.12.0.dev20260326+cpu | - | 19m34s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23595345537) | **克隆失败**: Ascend/pytorch 仓库克隆超时（网络问题） |
| 2026-03-26 11:29:50 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `91a4eb79` | 1h15m | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23591964908) | 无 |
| 2026-03-26 04:28:45 UTC | ❌ 失败 | 2.12.0.dev20260325+cpu | - | 38m33s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu-codex/actions/runs/23577538981) | **编译失败**: `Ascend910_95` not member of `SocVersion` (`ProcessGroupHCCL.cpp:430`) |
| 2026-03-07 14:31:31 UTC | ❌ 失败 | 2.12.0.dev20260306+cpu | - | 56m36s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800875730) | **编译失败**: `GroupInfo` has no member `rank_to_global_rank` (`NPUSHMEMSymmetricMemory.cpp`) |
| 2026-03-07 13:59:39 UTC | ❌ 失败 | 2.12.0.dev20260306+cpu | - | 10m12s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800386680) | **编译失败**: `CachingHostAllocator` API 重构 (`blocks`→`blocks_`, `process_events` 签名变更) |

---

## 详细分析

### 2026-03-28 04:52:35 UTC (Run #23677856986)

- **状态**: ✅ 成功
- **触发方式**: schedule (每日定时)
- **PyTorch Nightly**: `2.12.0.dev20260327+cpu`
- **Ascend/pytorch**: `cebf05bcc1516b345e84877f9f7052b59022b627` (2026-03-28 09:13:45 +0800)
- **构建时长**: 7m7s
- **发现问题**: 无

### 2026-03-27 22:23:34 UTC (Run #23670028060)

- **状态**: ✅ 成功
- **触发方式**: schedule (每日定时)
- **PyTorch Nightly**: `2.12.0.dev20260327+cpu`
- **Ascend/pytorch**: `f0c9bfe4230c87efc40f053bdd504434978800e9` (2026-03-27 21:59:21 +0800)
- **构建时长**: 1h13m
- **发现问题**: 无

### 2026-03-27 08:59:52 UTC (Run #23638769452)

- **状态**: ✅ 成功
- **触发方式**: schedule (每日定时)
- **PyTorch Nightly**: `2.12.0.dev20260326+cpu`
- **Ascend/pytorch**: `e787d68d1067d0eb4b12a6487e9cc7018ea26b69` (2026-03-26 22:40:35 +0800)
- **构建时长**: 7m20s
- **发现问题**: 无

### 2026-03-27 05:07:03 UTC (Run #23632119373)

- **状态**: ✅ 成功
- **触发方式**: schedule (每日定时)
- **PyTorch Nightly**: `2.12.0.dev20260326+cpu`
- **Ascend/pytorch**: `6c59120e91d53d593117fced1e1dc7cbe5f5ae1e` (2026-03-27 11:01:32 +0800)
- **构建时长**: 7m50s
- **发现问题**: 无

### 2026-03-27 01:36:32 UTC (Run #23626806955)

- **状态**: ✅ 成功
- **触发方式**: workflow_dispatch (手动触发)
- **PyTorch Nightly**: `2.12.0.dev20260326+cpu`
- **Ascend/pytorch**: `91a4eb79111203db803ba11f78d2703a4d964ec7` (2026-03-26 16:54:11 +0800)
- **构建时长**: 6m48s
- **发现问题**: 无

### 2026-03-26 22:20:03 UTC (Run #23620863183)

- **状态**: ✅ 成功
- **触发方式**: schedule (每日定时)
- **PyTorch Nightly**: `2.12.0.dev20260326+cpu`
- **Ascend/pytorch**: `e787d68d1067d0eb4b12a6487e9cc7018ea26b69` (2026-03-26 22:40:35 +0800)
- **构建时长**: 1h6m
- **发现问题**: 无

### 2026-03-26 12:53:45 UTC (Run #23595345537) ❌

- **状态**: ❌ 失败
- **触发方式**: workflow_dispatch (手动触发)
- **PyTorch Nightly**: `2.12.0.dev20260326+cpu`
- **失败步骤**: Clone Ascend/pytorch (with submodules)
- **构建时长**: 19m34s
- **发现问题**: **克隆失败** - Ascend/pytorch 仓库克隆超时（网络问题），非编译问题
- **Issue 操作**: 未创建 issue（非编译失败）

### 2026-03-26 11:29:50 UTC (Run #23591964908)

- **状态**: ✅ 成功
- **触发方式**: workflow_dispatch (手动触发)
- **PyTorch Nightly**: `2.12.0.dev20260326+cpu`
- **Ascend/pytorch**: `91a4eb79111203db803ba11f78d2703a4d964ec7` (2026-03-26 16:54:11 +0800)
- **构建时长**: 1h15m
- **发现问题**: 无

### 2026-03-26 04:28:45 UTC (Run #23577538981) ❌ [kerer-ai/pytorch-npu-codex]

- **状态**: ❌ 失败
- **触发方式**: schedule (每日定时)
- **PyTorch Nightly**: `2.12.0.dev20260325+cpu`
- **失败步骤**: Build torch_npu wheel
- **构建时长**: 38m33s
- **发现问题**: **编译失败** - `Ascend910_95` is not a member of `c10_npu::SocVersion`
- **受影响文件**: `torch_npu/csrc/distributed/ProcessGroupHCCL.cpp:430`
- **错误类型**: C1 API 删除（枚举成员移除）
- **Issue 操作**: 未创建 issue（不同仓库）

### 2026-03-07 14:31:31 UTC (Run #22800875730) ❌ [kerer-ai/pytorch-npu]

- **状态**: ❌ 失败
- **触发方式**: workflow_dispatch (手动触发)
- **PyTorch Nightly**: `2.12.0.dev20260306+cpu`
- **失败步骤**: Build torch_npu wheel
- **构建时长**: 56m36s
- **发现问题**: **编译失败** - `GroupInfo` has no member `rank_to_global_rank`
- **受影响文件**: `torch_npu/csrc/distributed/symm_mem/NPUSHMEMSymmetricMemory.cpp`
- **错误类型**: C1 API 删除（结构体成员移除）
- **Issue 操作**: 未创建 issue（不同仓库）

### 2026-03-07 13:59:39 UTC (Run #22800386680) ❌ [kerer-ai/pytorch-npu]

- **状态**: ❌ 失败
- **触发方式**: workflow_dispatch (手动触发)
- **PyTorch Nightly**: `2.12.0.dev20260306+cpu`
- **失败步骤**: Build torch_npu wheel
- **构建时长**: 10m12s
- **发现问题**: **编译失败** - `CachingHostAllocator` API 重构
  - `BlockPool::blocks` → `BlockPool::blocks_`
  - `BlockPool::unmapped` 成员移除
  - `process_events()` 签名变更（需要 pool 参数）
- **受影响文件**: `torch_npu/csrc/core/npu/CachingHostAllocator.cpp`
- **错误类型**: C1 API 删除 + C2 签名变更
- **Issue 操作**: 未创建 issue（不同仓库）

---

## 统计

- **总构建次数**: 11
- **成功次数**: 7
- **失败次数**: 4
- **成功率**: 63.6%
- **失败类型**: 网络问题（1次）、编译失败（3次）

---

## Open Issues

当前无 open issue。

---

> 报告更新时间: 2026-03-28