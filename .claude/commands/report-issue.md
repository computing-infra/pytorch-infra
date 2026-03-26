根据 CI 失败分析结果，在 `issues/` 目录下创建标准格式的 issue 记录文件。

## 前置条件

需要已知以下信息（通常来自 `/analyze-failure` 的输出）：

**构建信息：**
- Run ID、触发时间、运行时长
- Action 链接

**版本信息：**
- PyTorch nightly 版本号（如 `2.12.0.dev20260325+cpu`）
- Ascend/pytorch commit id 及提交时间（如 `b703a1a199e85347779124217f2330064f7fc284`）

**失败信息：**
- 受影响文件、API 变化详情、错误摘要

如果上述信息不明确，先运行 `/analyze-failure`。

> 先判断失败类型：
> - **兼容性失败（代码/API）**：写入 `issues/` 记录问题
> - **CI 脚本失败（workflow 语法/输出格式）**：优先修 workflow，通常不创建 `issues/` 兼容性条目

## 执行步骤

### 第一步：检查重复 issue

**必须先检查是否存在相同问题的 issue，避免重复创建。**

```bash
# 查看现有 issue 列表
ls -la issues/

# 根据受影响文件或错误关键词搜索
grep -l "ProcessGroupHCCL" issues/*.md 2>/dev/null
grep -l "SocVersion" issues/*.md 2>/dev/null
```

**去重判断标准：**
- 同一受影响文件 + 同一错误类型 → 视为重复，不创建
- 同一 API 变更导致的错误 → 视为重复，不创建
- 不同文件的不同错误 → 创建新 issue

**如果存在重复：**
- 告知用户已存在相关 issue 文件路径
- 如需更新，直接编辑现有文件而非新建

### 第二步：确定编号

```bash
date +%Y-%m-%d          # 获取今日日期
ls issues/              # 查看当天已有几个 issue，确定序号（001、002…）
```

### 第三步：创建 issue 文件

命名规则：`issues/YYYY-MM-DD-NNN-<受影响模块简述>.md`

使用以下模板填写，**所有字段都要有实质内容，不留占位符**：

```markdown
# [YYYY-MM-DD-NNN] <问题标题（含受影响类/文件名）>

## 构建信息

| 项目 | 详情 |
|------|------|
| 发现日期 | YYYY-MM-DD |
| 编号 | YYYY-MM-DD-NNN |
| Action 链接 | https://github.com/kerer-ai/pytorch-npu-codex/actions/runs/<run_id> |

## 版本信息

| 项目 | 详情 |
|------|------|
| PyTorch Nightly | `2.11.0.devYYYYMMDD` |
| Ascend/pytorch Commit | `abc123def456` (YYYY-MM-DD) |
| Commit 链接 | https://gitcode.com/Ascend/pytorch/commit/abc123def456 |

---

## 问题描述

（一段话：构建在哪个阶段失败，涉及什么模块，是什么类型的错误）

---

## 错误摘要

\```
<关键错误日志原文，3-5 条>
\```

---

## 根本原因

（说明是什么导致了失败，PyTorch 上游做了什么改动，Ascend 侧依赖了哪个已删除/变更的接口）

---

## 受影响范围

- **文件**：`<相对路径>`
- **涉及类/函数**：

---

## 建议修复方向

1. 具体建议
2. 注意事项

> **注意**：此问题需在 Ascend/pytorch 上游仓库修复，本项目仅进行每日验证。
```

### 第四步：提交到远端

创建 issue 文件后，提交并推送到远程仓库：

```bash
git add issues/YYYY-MM-DD-NNN-*.md
git commit -m "docs: 添加 issue 记录 <问题描述简述>"
git push
```

### 第五步：完成后输出

告知用户：
- issue 文件路径
- 已提交到远端
- 提醒问题需在 Ascend/pytorch 上游仓库修复

## 何时不创建 issue（新增）

以下情况通常不创建 `issues/YYYY-MM-DD-NNN-*.md`：
- 日志明确显示 wheel 已构建成功，但 step 因 `GITHUB_OUTPUT` / `Invalid format` 失败
- artifact 上传、summary 渲染、缓存步骤等基础设施问题

这类问题应直接提交 workflow 修复，并在提交信息中说明根因与影响范围。
