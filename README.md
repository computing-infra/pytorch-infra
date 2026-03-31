# pytorch-infra

每日自动验证 [Ascend/pytorch](https://gitcode.com/Ascend/pytorch) 与 PyTorch nightly 版本的编译兼容性，以及代码静态扫描。

## Workflow 流程

### 每日构建验证

```
每日三次自动触发（北京时间 06:00 / 11:00 / 16:00）
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

### 代码静态扫描

```
每周一自动触发（北京时间 18:00）
            │
            ▼
┌─────────────────────────────────┐
│  1. 克隆 Ascend/pytorch          │
│  2. 应用 lint 配置               │
│  3. 执行代码静态扫描              │
│  4. 生成报告 & 创建 issue         │
└─────────────────────────────────┘
```

**检查项目：**
| Linter | 功能 |
|--------|------|
| FLAKE8 | Python PEP8 代码检查 |
| CLANGFORMAT | C++ 代码格式化检查 |
| NEWLINE | 换行符检查（确保 LF） |
| SPACES | 尾部空格检查 |
| TABS | Tab 检查（应使用空格） |

## 构建结果

| 状态 | 说明 |
|------|------|
| ✅ 成功 | 生成 `dist/*.whl`，可下载 |
| ❌ 失败 | 下载 `build-log` artifact 查看编译错误 |

## 问题分析工具

本仓库内置 Claude Code slash commands，用于分析 CI 构建：

| 命令 | 用途 |
|------|------|
| `/analyze-failure` | 分析最新 CI 构建：失败时创建 issue，成功时关闭已修复的 |
| `/sync-issues` | 将 GitHub issue 同步到 GitCode（`Ascend/pytorch`） |
| `/scheduled-ci-analysis` | 创建定时任务：每日三次自动执行 `/analyze-failure`（北京时间 08:00/13:00/18:00） |

**典型流程：** `/analyze-failure` → `/sync-issues`