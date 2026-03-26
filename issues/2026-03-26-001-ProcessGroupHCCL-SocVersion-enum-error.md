# [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值

- **发现日期**：2026-03-26
- **编号**：2026-03-26-001
- **严重级别**：🔴 编译失败
- **受影响文件**：
  - `torch_npu/csrc/distributed/ProcessGroupHCCL.cpp`
- **触发版本**：PyTorch nightly 2026-03-26
- **对应 patch**：无（Ascend/pytorch 自身代码问题）

---

## 问题描述

构建在编译阶段失败，`ProcessGroupHCCL.cpp` 第 430 行引用了不存在的枚举值 `c10_npu::SocVersion::Ascend910_95`，导致编译错误。这是 Ascend/pytorch 代码内部不一致问题，`NpuVariables.h` 中枚举定义已变更为 `Ascend950`，但 `ProcessGroupHCCL.cpp` 未同步更新。

---

## 根本原因分析

### 1. 枚举值命名不一致

`ProcessGroupHCCL.cpp:430` 使用了 `Ascend910_95` 作为比较边界：

```cpp
return ((soc_version >= c10_npu::SocVersion::Ascend910B1) && (soc_version < c10_npu::SocVersion::Ascend310B1)) ||
        ((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend910_95));
```

但 `NpuVariables.h` 中 `SocVersion` 枚举定义为：

```cpp
Ascend910_9391 = 250,
Ascend910_9392,
Ascend910_9381,
Ascend910_9382,
Ascend910_9372,
Ascend910_9362,
Ascend950 = 260      // 没有 Ascend910_95
```

关键错误日志：
```
ProcessGroupHCCL.cpp:430:110: error: 'Ascend910_95' is not a member of 'c10_npu::SocVersion'; did you mean 'Ascend910A'?
make[2]: *** [CMakeFiles/torch_npu.dir/build.make:13869: CMakeFiles/torch_npu.dir/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp.o] Error 1
```

---

## 修复方案

在 Ascend/pytorch 中将 `Ascend910_95` 替换为 `Ascend950`：

```cpp
// 修复前
((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend910_95));

// 修复后
((soc_version >= c10_npu::SocVersion::Ascend910_9391) && (soc_version < c10_npu::SocVersion::Ascend950));
```

> **注意**：此问题需在 Ascend/pytorch 上游仓库修复，本项目仅进行每日验证，不直接修改上游代码。建议向 Ascend/pytorch 提交 issue 或 PR。