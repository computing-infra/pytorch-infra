分析最新一次 GitHub Actions CI 构建，根据结果执行不同操作：失败时分析原因并创建 issue，成功时检查并关闭已修复的 issue。

---

## 前置检查

### 检查 GitHub CLI 登录状态

```bash
gh auth status
```

| 输出内容 | 状态 | 处理方式 |
|----------|------|----------|
| `Logged in to github.com` | ✅ 已登录 | 继续执行 |
| `not logged in` | ❌ 未登录 | 提示运行 `gh auth login` |
| `token expired` | ❌ token 过期 | 提示运行 `gh auth refresh` |
| `command not found` | ❌ gh 未安装 | 提示安装 GitHub CLI |

---

## 执行流程

```
获取最新 CI 构建
       │
       ├── ❌ 失败 ──→ 分析失败原因 → 创建 GitHub issue
       │
       └── ✅ 成功 ──→ 检查 open issue → 关闭已修复的 issue
```

---

## 模式一：构建失败 → 分析 + 创建 issue

### 第一步：获取最新失败 Run

```bash
gh run list --repo computing-infra/pytorch-infra --limit 5
```

记录最新一条失败 Run 的 ID 和触发时间。

**构建进度判断：**
- `< 2 分钟` → 早期失败（checkout、依赖安装）
- `2-10 分钟` → 中期失败（PyTorch 安装、代码克隆）
- `> 30 分钟` → 编译阶段失败（API 不兼容）

### 第二步：提取版本信息

```bash
# PyTorch nightly 版本
gh run view <run_id> --repo computing-infra/pytorch-infra --log 2>&1 \
  | grep -E "PyTorch nightly version:" | head -1

# Ascend/pytorch commit
gh run view <run_id> --repo computing-infra/pytorch-infra --log 2>&1 \
  | grep -E "Ascend/pytorch commit:" | head -1
```

### 第三步：拉取失败日志并诊断

```bash
# 获取失败日志
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 | head -300

# 检查失败特征
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 \
  | grep -E "error:|make\[.*\]:|Invalid format|GITHUB_OUTPUT|Permission denied|exceeded the maximum|Unable to locate|Connection refused" \
  | head -30
```

**失败类型分类：**

| 类型 | 特征关键词 | 操作 |
|------|------------|------|
| **编译失败** | `error:`、`fatal error` | 创建 issue |
| **Workflow 脚本失败** | `Invalid format`、`GITHUB_OUTPUT` | 直接修 workflow |
| **依赖安装失败** | `Unable to locate package` | 检查外部服务 |
| **超时失败** | `exceeded the maximum` | 调整 timeout |
| **网络问题** | `Connection refused`、`timed out` | 重试 |

**编译失败二级分类：**

| 子类型 | 特征日志 | 修复方向 |
|--------|----------|----------|
| C1 API 删除 | `has no member named`、`is not a member of` | 查找替代 API |
| C2 签名变更 | `marked 'override', but does not override` | 更新签名 |
| C3 接口新增 | `abstract class type` | 补充实现 |
| C4 头文件变更 | `file not found` | 调整路径 |
| C5 类型不兼容 | `cannot convert` | 适配新类型 |
| C6 链接错误 | `undefined reference` | 检查依赖 |

### 第四步：检查重复 issue

```bash
gh issue list -R computing-infra/pytorch-infra --state open --limit 50
```

**去重标准：**
- 标题相同或高度相似 → 视为重复
- 同一受影响文件 + 同一错误类型 → 视为重复

### 第五步：创建 GitHub issue

**仅编译失败创建 issue，其他类型直接处理。**

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
| PyTorch Nightly | `版本号` |
| Ascend/pytorch Commit | `commit` (日期) |
| Commit 链接 | https://gitcode.com/Ascend/pytorch/commit/xxx |

---

## 问题描述

（构建在哪个阶段失败，涉及什么模块）

---

## 错误摘要

\`\`\`
<关键错误日志，3-5 条>
\`\`\`

---

## 根本原因

（说明失败原因）

---

## 受影响范围

- **文件**：`相对路径`
- **涉及类/函数**：

---

## 建议修复方向

1. 具体建议
2. 注意事项

> **注意**：此问题需在 Ascend/pytorch 上游仓库修复。
EOF
)" \
  --label "bug,nightly-ci"
```

---

## 模式二：构建成功 → 关闭已修复 issue

### 第一步：获取当前构建信息

```bash
gh run list --repo computing-infra/pytorch-infra --limit 1
```

提取 Run ID 和版本信息。

### 第二步：获取 open issue 列表

```bash
gh issue list -R computing-infra/pytorch-infra --state open --limit 50
```

### 第三步：检查每个 issue 是否应关闭

对于每个 open issue：

1. **提取特征**：受影响文件、错误类型、关键标识符
2. **检查构建日志**：错误是否仍存在

```bash
gh run view <run_id> --repo computing-infra/pytorch-infra --log > /tmp/build.log
grep -E "<关键错误特征>" /tmp/build.log
```

**关闭条件：**
- 构建成功，且错误未在日志中出现

### 第四步：关闭已修复 issue

```bash
gh issue close <issue_id> -R computing-infra/pytorch-infra \
  --comment "✅ **自动关闭：问题已修复**

验证构建：
- PyTorch Nightly: \`版本\`
- Ascend/pytorch Commit: \`commit\`
- 验证 Run: #<run_id>

该问题已不再出现。"
```

---

## 输出报告

```
## CI 分析报告

### 构建结果: ❌ 失败 / ✅ 成功

### 版本信息
- PyTorch Nightly: `版本`
- Ascend/pytorch Commit: `commit`

### 失败分析（失败时）
- 失败类型: 编译失败 / Workflow 失败 / ...
- 受影响文件: xxx.cpp
- 根本原因: API 删除

### Issue 操作
- 新建: #123
- 关闭: #456 (已修复)
- 保持: #789 (错误仍存在)
```

---

## 注意事项

- 编译失败 → 创建 issue
- Workflow 失败 → 直接修复 workflow
- 关闭 issue 时必须添加评论说明原因
- 如有误关闭，可手动重新开启