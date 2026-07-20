# pytorch-infra

监控 [Ascend/pytorch](https://github.com/Ascend/pytorch) 仓库 `pytorch_ci_trigger.yml` GitHub Actions 执行结果，对异常失败进行 AI 分析、飞书通知，并支持一键提交 GitCode issue。

## 架构

```
pytorch_ci_trigger.yml (Ascend/pytorch)
        │ 失败
        ▼
┌─────────────────────────────────────────┐
│ ci-monitor.yml (定时 北京 09/15/21)      │
│  扫描失败 → 提取日志 → 下载源码          │
│  → opencode + skill AI 分析 → 生成报告   │
│  → commit 到 reports/ → 飞书通知         │
└─────────────────────────────────────────┘
        │ reports/{run_id}.md
        ▼
┌─────────────────────────────────────────┐
│ issue-create.yml (手动触发)              │
│  找最新报告 → 按 run_name 去重            │
│  → opencode + skill 创建 GitCode issue   │
└─────────────────────────────────────────┘
```

## 目录结构

| 路径 | 说明 |
|------|------|
| `.github/workflows/ci-monitor.yml` | 定时监控 workflow |
| `.github/workflows/issue-create.yml` | 手动 issue 创建 workflow |
| `skills/ascend-ci-build-debugger/` | build 阶段失败分析 skill |
| `skills/gitcode-issue-create/` | GitCode issue 创建 skill |
| `scripts/` | 工具脚本（扫描/提取/通知等） |
| `reports/` | AI 分析报告（运行时生成） |

## 所需 GitHub Secrets

| Secret | 用途 |
|--------|------|
| `BAILIAN_API_KEY` | opencode 调用稀宇 MiniMax-M3 模型（通过 `{env:}` 引用，不落盘） |
| `GC_TOKEN` | GitCode CLI 认证（创建 issue） |
| `FEISHU_WEBHOOK` | 飞书机器人 webhook URL |

> 读取 Ascend/pytorch Actions 数据使用 GitHub Actions 自动提供的 `GITHUB_TOKEN`，无需额外 PAT。

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt  # 如有

# 手动测试扫描脚本
python3 scripts/scan_failures.py

# 手动测试报告查找
python3 scripts/find_latest_report.py
```
