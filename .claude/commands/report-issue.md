根据 CI 失败分析结果，在 `issues/` 目录下创建标准格式的 issue 记录文件。

## 前置条件

需要已知以下信息（通常来自 `/analyze-failure` 的输出）：
- 失败日期、受影响文件、API 变化详情、错误摘要

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

- **发现日期**：YYYY-MM-DD
- **编号**：YYYY-MM-DD-NNN
- **严重级别**：🔴 编译失败 / 🟡 编译警告 / 🟢 运行时问题
- **受影响文件**：
  - `相对/路径/文件1.cpp`
  - `相对/路径/文件2.hpp`（如有）
- **触发版本**：PyTorch nightly YYYY-MM-DD

---

## 问题描述

（一段话：构建在哪个阶段失败，涉及什么模块，是什么类型的错误）

---

## 根本原因分析

### 1. <原因标题>

（说明 PyTorch 上游做了什么改动，Ascend 侧依赖了哪个已删除/变更的接口）

关键错误日志：
\```
error: 'struct X' has no member named 'Y'
\```

### 2. <原因标题>（如有多个独立原因）

（同上）

---

## 修复方案

建议的修复方式：

1. **改动1**：（说明需要做什么改动）
2. **改动2**：（同上）

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
