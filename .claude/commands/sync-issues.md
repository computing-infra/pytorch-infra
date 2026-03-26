本地 issues 与 GitCode 平台（`Ascend/pytorch` 仓库）的双向同步工具。

**功能：**
1. **本地 → GitCode**：将新 issue 同步创建到 GitCode
2. **GitCode → 本地**：同步远程 issue 状态（关闭、解决等）

---

## 前置检查

### 步骤 0：检查 GitCode CLI 登录状态

**必须先验证 gc 命令可用且已登录，否则无法操作 GitCode。**

```bash
gc auth status
```

| 输出内容 | 状态 | 处理方式 |
|----------|------|----------|
| `Logged in as` | ✅ 已登录 | 继续执行 |
| `not logged in` | ❌ 未登录 | 提示用户运行 `gc auth login` |
| `token expired` | ❌ token 过期 | 提示用户重新登录 |
| `command not found` | ❌ gc 未安装 | 提示用户安装 GitCode CLI |

---

## 执行步骤

### 第一步：获取远程 issue 列表

**获取 GitCode 上所有 issue 及其状态：**

```bash
gc issue list -R Ascend/pytorch --limit 100
```

解析输出，提取每个 issue 的：
- ID
- 标题
- 状态（open/closed）
- URL

---

### 第二步：扫描本地 issues 目录

```bash
ls issues/*.md 2>/dev/null
```

---

### 第三步：同步本地 issue 到 GitCode

对每个本地 issue 文件执行：

#### 3.1 检查是否已同步

读取文件开头的 frontmatter：

```markdown
---
gitcode_issue_id: 123
gitcode_issue_status: open
---
```

- **无 `gitcode_issue_id`**：需要创建新 issue
- **有 `gitcode_issue_id`**：跳过创建，进入状态同步

#### 3.2 创建新 issue

对于未同步的文件：

```bash
gc issue create -R Ascend/pytorch \
  --title "[Bug] <title>" \
  --body "$(cat <file_path>)"
```

创建成功后，提取 issue ID，更新本地文件：

```markdown
---
gitcode_issue_id: 123
gitcode_issue_status: open
---

# [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值

...（原有内容）
```

#### 3.3 添加标签

```bash
gc issue label <issue_number> --add ai-analyze,nightly-ci,bug -R Ascend/pytorch
```

---

### 第四步：同步 GitCode 状态到本地

对于已有 `gitcode_issue_id` 的本地文件，检查远程状态：

```bash
gc issue view <issue_id> -R Ascend/pytorch
```

**状态映射：**

| 远程状态 | 本地状态 | 操作 |
|----------|----------|------|
| open | open | 无需更新 |
| closed | open | 更新本地状态为 closed |
| open | closed | 无需更新（本地状态较旧） |

**更新本地文件：**

```markdown
---
gitcode_issue_id: 123
gitcode_issue_status: closed
---

# [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值

> **状态**：✅ 已在 GitCode 关闭
> **链接**：https://gitcode.com/Ascend/pytorch/issues/123

...（原有内容）
```

---

### 第五步：提交本地更新

如果有文件更新：

```bash
git add issues/*.md
git commit -m "chore: 同步 GitCode issue 状态"
git push
```

---

### 第六步：输出同步结果

```
## 同步结果

### 新建 issues (X 个)
- #123: [2026-03-26-001] ProcessGroupHCCL 枚举错误
  https://gitcode.com/Ascend/pytorch/issues/123

### 状态变更 (Y 个)
- #456: open → closed
  https://gitcode.com/Ascend/pytorch/issues/456

### 无变化 (Z 个)
- #789: open
- #100: closed
```

---

## 去重机制

### 检查优先级

| 优先级 | 检查点 | 条件 | 操作 |
|--------|--------|------|------|
| 1 | 本地 frontmatter | 存在 `gitcode_issue_id` | 跳过创建，仅同步状态 |
| 2 | 标题精确匹配 | 标题完全相同 | 更新本地 frontmatter |
| 3 | 语义相似度 | ≥ 70% | 更新本地 frontmatter |
| 4 | 都不满足 | — | 创建新 issue |

### 语义相似度计算

| 检查项 | 权重 |
|--------|------|
| 受影响文件相同 | 40% |
| 错误类型相同 | 30% |
| 关键标识符相同 | 30% |

---

## Frontmatter 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `gitcode_issue_id` | int | GitCode issue 编号 |
| `gitcode_issue_status` | string | `open` 或 `closed` |

---

## 注意事项

- 每次执行都以 `gc issue list` 的**实时结果**为准
- 创建新 issue 后，以 `gc issue create` 返回的 ID 写入 frontmatter
- 状态同步是单向的：GitCode → 本地
- 所有 issue 统一添加 `ai-analyze`、`nightly-ci` 和 `bug` 标签