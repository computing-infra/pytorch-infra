---
gitcode_issue_id: 3
---

# [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值

## 构建信息

| 项目 | 详情 |
|------|------|
| 发现日期 | 2026-03-26 |
| 编号 | 2026-03-26-001 |
| Action 链接 | https://github.com/kerer-ai/pytorch-npu-codex/actions/runs/23577538981 |

## 版本信息

| 项目 | 详情 |
|------|------|
| PyTorch Nightly | `2.12.0.dev20260325+cpu` |
| Ascend/pytorch Commit | `ef23cce690d51c2d449a393315f91a9a053056fd` (2026-03-26) |
| Commit 链接 | https://gitcode.com/Ascend/pytorch/commit/ef23cce690d51c2d449a393315f91a9a053056fd |

---

## 问题描述

构建在编译阶段失败，`ProcessGroupHCCL.cpp` 第 430 行引用了不存在的枚举值 `c10_npu::SocVersion::Ascend910_95`，导致编译错误。这是 Ascend/pytorch 代码内部不一致问题，`NpuVariables.h` 中枚举定义已变更为 `Ascend950`，但 `ProcessGroupHCCL.cpp` 未同步更新。

---

## 错误摘要

```
ProcessGroupHCCL.cpp:430:110: error: 'Ascend910_95' is not a member of 'c10_npu::SocVersion'; did you mean 'Ascend910A'?

  430 | ((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend910_95));
```

---

## 根本原因

`ProcessGroupHCCL.cpp:430` 在 `IsCompatibleSoc()` 函数中使用 `Ascend910_95` 作为比较边界：

```cpp
return ((soc_version >= c10_npu::SocVersion::Ascend910B1) && (soc_version < c10_npu::SocVersion::Ascend310B1)) ||
        ((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend910_95));
```

但 `NpuVariables.h` 中 `SocVersion` 枚举已重命名，`Ascend910_95` 不存在，应为 `Ascend950`：

```cpp
Ascend910_9391 = 250,
Ascend910_9392,
Ascend910_9381,
Ascend910_9382,
Ascend910_9372,
Ascend910_9362,
Ascend950 = 260      // 没有 Ascend910_95
```

---

## 受影响范围

- **文件**：`torch_npu/csrc/distributed/ProcessGroupHCCL.cpp`
- **涉及函数**：`IsCompatibleSoc()`

---

## 建议修复方向

将 `Ascend910_95` 替换为 `Ascend950`：

```cpp
// 修复前
((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend910_95));

// 修复后
((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend950));
```

> **注意**：此问题需在 Ascend/pytorch 上游仓库修复，本项目仅进行每日验证。