# CI 分析报告

本报告记录 Ascend/pytorch 与 PyTorch Nightly 的每日集成验证结果。

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

## 执行记录

| 执行时间 | 状态 | PyTorch Nightly | Ascend/pytorch Commit | 构建时长 | Action 链接 | 发现问题 | Issue |
|----------|------|-----------------|----------------------|----------|-------------|----------|-------|
| 2026-03-28 04:52:35 UTC | ✅ 成功 | 2.12.0.dev20260327+cpu | `cebf05bc` | 7m7s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23677856986) | 无 | |
| 2026-03-27 22:23:34 UTC | ✅ 成功 | 2.12.0.dev20260327+cpu | `f0c9bfe4` | 1h13m | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23670028060) | 无 | |
| 2026-03-27 08:59:52 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `e787d68d` | 7m20s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23638769452) | 无 | |
| 2026-03-27 05:07:03 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `6c59120e` | 7m50s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23632119373) | 无 | |
| 2026-03-27 01:36:32 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `91a4eb79` | 6m48s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23626806955) | 无 | |
| 2026-03-26 22:20:03 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `e787d68d` | 1h6m | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23620863183) | 无 | |
| 2026-03-26 12:53:45 UTC | ❌ 失败 | 2.12.0.dev20260326+cpu | - | 19m34s | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23595345537) | **克隆失败**: Ascend/pytorch 仓库克隆超时（网络问题） | |
| 2026-03-26 11:29:50 UTC | ✅ 成功 | 2.12.0.dev20260326+cpu | `91a4eb79` | 1h15m | [查看执行记录](https://github.com/computing-infra/pytorch-infra/actions/runs/23591964908) | 无 | |
| 2026-03-26 04:28:45 UTC | ❌ 失败 | 2.12.0.dev20260325+cpu | - | 38m33s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu-codex/actions/runs/23577538981) | **编译失败**: `Ascend910_95` not member of `SocVersion` (`ProcessGroupHCCL.cpp:430`) | |
| 2026-03-07 14:31:31 UTC | ❌ 失败 | 2.12.0.dev20260306+cpu | - | 56m36s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800875730) | **编译失败**: `GroupInfo` has no member `rank_to_global_rank` (`NPUSHMEMSymmetricMemory.cpp`) | |
| 2026-03-07 13:59:39 UTC | ❌ 失败 | 2.12.0.dev20260306+cpu | - | 10m12s | [查看执行记录](https://github.com/kerer-ai/pytorch-npu/actions/runs/22800386680) | **编译失败**: `CachingHostAllocator` API 重构 (`blocks`→`blocks_`, `process_events` 签名变更) | |

---

> 报告更新时间: 2026-03-28