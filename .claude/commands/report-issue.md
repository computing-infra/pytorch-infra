根据 CI 构建结果管理 GitHub issue：创建新 issue 或关闭已修复的 issue。

---

## 执行模式

根据当前构建结果选择不同操作：

| 构建结果 | 操作 |
|----------|------|
| ❌ 失败 | 创建新 issue |
| ✅ 成功 | 检查并关闭已修复的 issue |

---

## 模式一：构建失败 → 创建 issue

### 前置条件

需要已知以下信息（通常来自 `/analyze-failure` 的输出）：

**构建信息：**
- Run ID、触发时间、运行时长
- Action 链接

**版本信息：**
- PyTorch nightly 版本号
- Ascend/pytorch commit id 及提交时间

**失败信息：**
- 受影响文件、API 变化详情、错误摘要

如果上述信息不明确，先运行 `/analyze-failure`。

### 步骤 1：检查重复 issue

```bash
gh issue list -R computing-infra/pytorch-infra --state open --limit 50
```

**去重判断标准：**
- 标题相同或高度相似 → 视为重复，不创建
- 同一受影响文件 + 同一错误类型 → 视为重复，不创建

**如果存在重复：**
- 告知用户已存在相关 issue 链接
- 不创建新 issue

### 步骤 2：创建 GitHub issue

```bash
gh issue create -R computing-infra/pytorch-infra \
  --title "[Bug] <问题标题（含受影响类/文件名）>" \
  --body "$(cat <<'EOF'
## 构建信息

| 项目 | 详情 |
|------|------|
| 发现日期 | YYYY-MM-DD |
| Action 链接 | https://github.com/computing-infra/pytorch-infra/actions/runs/<run_id> |

## 版本信息

| 项目 | 详情 |
|------|------|
| PyTorch Nightly | `2.12.0.devYYYYMMDD+cpu` |
| Ascend/pytorch Commit | `abc123def456` (YYYY-MM-DD) |
| Commit 链接 | https://gitcode.com/Ascend/pytorch/commit/abc123def456 |

---

## 问题描述

（一段话：构建在哪个阶段失败，涉及什么模块，是什么类型的错误）

---

## 错误摘要

\`\`\`
<关键错误日志原文，3-5 条>
\`\`\`

---

## 根本原因

（说明是什么导致了失败）

---

## 受影响范围

- **文件**：`<相对路径>`
- **涉及类/函数**：

---

## 建议修复方向

1. 具体建议
2. 注意事项

> **注意**：此问题需在 Ascend/pytorch 上游仓库修复，本项目仅进行每日验证。
EOF
)" \
  --label "bug,nightly-ci"
```

---

## 模式二：构建成功 → 关闭已修复 issue

### 步骤 1：获取当前构建信息

提取当前构建的版本信息：

```bash
# 从 CI 日志或环境获取
TORCH_VERSION="<当前 PyTorch nightly 版本>"
ASCEND_COMMIT="<当前 Ascend/pytorch commit>"
```

### 步骤 2：获取所有 open 状态的 issue

```bash
gh issue list -R computing-infra/pytorch-infra --state open --limit 50
```

解析每个 issue 的：
- Issue ID
- 标题
- Body（包含受影响文件、错误类型等信息）

### 步骤 3：检查是否需要关闭

对于每个 open issue，执行以下检查：

#### 3.1 提取 issue 特征

从 issue body 提取：
- **受影响文件**：如 `ProcessGroupHCCL.cpp`
- **错误类型**：如 `API 删除`、`签名变更`、`枚举值不存在`
- **关键标识符**：如 `SocVersion::Ascend910_95`

#### 3.2 判断是否应该关闭

**关闭条件（满足任一）：**

| 条件 | 说明 |
|------|------|
| 构建成功 | 整体构建成功，无任何编译错误 |
| 错误未重现 | 当前构建日志中不存在该 issue 描述的错误 |

**检查方法：**

```bash
# 获取当前构建日志
gh run view <run_id> --repo computing-infra/pytorch-infra --log > /tmp/current_build.log

# 检查错误是否仍存在
grep -E "<关键错误特征>" /tmp/current_build.log
```

- **无匹配**：错误已修复，可以关闭 issue
- **有匹配**：错误仍存在，保持 issue open

### 步骤 4：关闭 issue

对于判定为已修复的 issue：

```bash
gh issue close <issue_id> -R computing-infra/pytorch-infra \
  --comment "✅ **自动关闭：问题已修复**

构建成功验证：
- PyTorch Nightly: \`<版本>\`
- Ascend/pytorch Commit: \`<commit>\`
- 验证构建: #<run_id>

该问题在上述版本中已不再出现，自动标记为已修复。"
```

### 步骤 5：输出结果

```
## Issue 状态更新

### 已关闭（已修复）
- #123: ProcessGroupHCCL 枚举错误
  原因：当前构建成功，错误未重现

### 保持开启
- #456: 其他问题
  原因：错误仍在当前构建中出现
```

---

## 判断流程图

```
构建结果
    │
    ├─ ❌ 失败
    │      │
    │      ▼
    │   检查重复 issue
    │      │
    │      ├─ 存在重复 → 跳过
    │      └─ 无重复 → 创建新 issue
    │
    └─ ✅ 成功
           │
           ▼
        获取 open issue 列表
           │
           ▼
        对每个 issue 检查错误是否仍存在
           │
           ├─ 错误已消失 → 关闭 issue
           └─ 错误仍存在 → 保持开启
```

---

## 何时不创建 issue

以下情况通常不创建 issue：
- 日志明确显示 wheel 已构建成功，但 step 因 `GITHUB_OUTPUT` / `Invalid format` 失败
- artifact 上传、summary 渲染、缓存步骤等基础设施问题

这类问题应直接提交 workflow 修复。

---

## 注意事项

- 关闭 issue 时必须添加评论说明原因
- 评论中包含验证通过的版本信息
- 如有误关闭，可手动重新开启