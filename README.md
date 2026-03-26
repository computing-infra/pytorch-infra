# pytorch-infra

每日自动验证 [Ascend/pytorch](https://gitcode.com/Ascend/pytorch) 与 PyTorch nightly 版本的编译兼容性。

## Workflow 流程

```
每日 UTC 21:00（北京时间 05:00）自动触发
            │
            ▼
┌─────────────────────────────────┐
│  1. 安装 PyTorch nightly (CPU)   │
│  2. 克隆 Ascend/pytorch + 子模块 │
│  3. 编译 CANN 桩库               │
│  4. 构建 torch_npu wheel         │
│  5. 上传构建产物                  │
└─────────────────────────────────┘
            │
            ▼
      构建结果通知
```

**关键特性：**
- **无 CANN 依赖**：使用内置桩库编译，仅需 GCC
- **ccache 加速**：二次构建命中率 ~99%
- **手动触发**：Actions 页面点击 **Run workflow**，可选指定 PyTorch nightly 日期

## 构建结果

| 状态 | 说明 |
|------|------|
| ✅ 成功 | 生成 `dist/*.whl`，可下载 |
| ❌ 失败 | 下载 `build-log` artifact 查看编译错误 |

## 问题分析工具

本仓库内置 Claude Code slash commands，用于分析 CI 失败：

| 命令 | 用途 |
|------|------|
| `/analyze-failure` | 拉取日志、定位根因、输出结构化报告 |
| `/report-issue` | 失败时创建 issue，成功时关闭已修复的 |
| `/sync-issues` | 将 GitHub issue 同步到 GitCode（`kerer-sk/pytorch`） |

**典型流程：** CI 失败 → `/analyze-failure` → `/report-issue` → `/sync-issues`