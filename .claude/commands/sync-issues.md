将本地 `issues/` 目录下的 issue 文档同步提交到 GitCode 平台（`kerer-sk/pytorch` 仓库）。

---

## 前置检查

### 步骤 0：检查 GitCode CLI 登录状态

**必须先验证 gc 命令可用且已登录，否则无法操作 GitCode。**

```bash
gc auth status
```

**判断结果：**

| 输出内容 | 状态 | 处理方式 |
|----------|------|----------|
| `Logged in as` | ✅ 已登录 | 继续执行 |
| `not logged in` | ❌ 未登录 | 提示用户运行 `gc auth login` |
| `token expired` | ❌ token 过期 | 提示用户重新登录 |
| `command not found` | ❌ gc 未安装 | 提示用户安装 GitCode CLI |

**如果未登录，告知用户：**
```
GitCode CLI 未登录，请先执行：
  gc auth login
```

---

## 执行步骤

### 第一步：扫描本地 issues 目录

获取所有待同步的 issue 文件：

```bash
ls issues/*.md
```

记录文件列表，逐个处理。

---

### 第二步：获取远程仓库现有 issues

**获取远程 issue 列表用于去重检查：**

```bash
gc issue list -R kerer-sk/pytorch --limit 100
```

解析输出，提取所有已存在的 issue 标题列表 `remote_titles[]`。

---

### 第三步：逐个处理本地 issue

对每个本地 issue 文件执行以下逻辑：

#### 3.1 检查本地是否已同步

读取文件开头，检查是否包含 frontmatter：

```markdown
---
gitcode_issue_id: 123
---
```

- **已有 `gitcode_issue_id`**：跳过，输出 `已同步: issue #<id>`
- **无此字段**：继续下一步

#### 3.2 提取 issue 信息

从文件内容提取：

1. **标题**：第一行 `# [...]` 中的内容（去掉 `# ` 前缀）
   - 例如：`# [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值`
   - 提取为：`[2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值`

2. **正文**：文件全部内容（包含标题行）

#### 3.3 检查远程是否已存在

**需要进行语义匹配，而不仅是标题匹配**（可能存在人工提交的 issue，标题不同但内容相同）。

**语义匹配检查项：**

1. **受影响文件**：提取本地 issue 中的「受影响文件」字段，与远程 issue body 对比
2. **错误类型**：对比根本原因中的错误类型（如 API 删除、签名变更、枚举值重命名）
3. **关键标识符**：对比关键类名、函数名、API 名称、枚举值等

**匹配流程：**

```
1. 标题精确匹配 → 直接认定为重复
2. 标题不匹配 → 语义检查：
   a. 提取本地 issue 的「受影响文件」「错误类型」「关键标识符」
   b. 对每个远程 issue 进行语义比对
   c. 计算相似度：
      - 受影响文件相同 → +40%
      - 错误类型相同 → +30%
      - 关键标识符相同 → +30%
   d. 相似度 ≥ 70% → 认定为语义重复
```

**处理方式：**

- **标题精确匹配 或 语义相似度 ≥ 70%**：
  1. 提取远程 issue ID
  2. 更新本地文件，添加 `gitcode_issue_id` frontmatter
  3. 输出 `远程已存在: <title> → #<id> (相似度: XX%)`
  4. 标记需要提交更新
- **不匹配**：准备创建新 issue

#### 3.4 创建远程 issue 并添加标签

**注意**：`gc issue create` 的 `--label` 参数可能不支持，需分两步执行。

**步骤 1：创建 issue**

```bash
gc issue create -R kerer-sk/pytorch \
  --title "[Bug] <title>" \
  --body "$(cat <file_path>)"
```

输出示例：
```
✓ Created issue #123 in kerer-sk/pytorch
  https://gitcode.com/kerer-sk/pytorch/issues/123
```

**步骤 2：添加标签**

从输出提取 issue 编号后，添加标签：

```bash
gc issue label <issue_number> --add ai-analyze,nightly-ci,bug -R kerer-sk/pytorch
```

输出示例：
```
✓ Added labels to issue #123: ai-analyze, nightly-ci, bug
```

#### 3.5 记录同步结果

创建成功后，gc 会输出新 issue 的 URL 和编号：

```
https://gitcode.com/kerer-sk/pytorch/issues/123
```

提取 issue ID（如 `123`），更新本地文件，在开头添加 frontmatter：

```markdown
---
gitcode_issue_id: 123
---

# [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值

...（原有内容）
```

---

### 第四步：提交本地更新

如果本地文件有更新（新建 issue 或远程已存在），提交到远端：

```bash
git add issues/*.md
git commit -m "chore: 更新 issue 同步状态"
git push
```

---

### 第五步：输出同步结果摘要

处理完成后，输出：

```
## 同步结果

- 新建: X 个
- 已同步: Y 个
- 远程已存在: Z 个

### 新建 issues
- #123: [2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值
  https://gitcode.com/kerer-sk/pytorch/issues/123

### 跳过（已同步）
- issues/2026-03-07-001-xxx.md → #456

### 跳过（远程已存在）
- issues/xxx.md
```

---

## 去重机制总结

### 检查优先级

| 优先级 | 检查点 | 条件 | 操作 |
|--------|--------|------|------|
| 1 | 本地 frontmatter | 存在 `gitcode_issue_id` | **直接跳过**，无需检查远程 |
| 2 | 标题精确匹配 | 标题完全相同 | 认定为重复，更新本地 |
| 3 | 语义相似度 | ≥ 70% | 认定为重复，更新本地 |
| 4 | 都不满足 | — | 创建新 issue |

### 语义相似度计算

| 检查项 | 权重 | 示例 |
|--------|------|------|
| 受影响文件相同 | 40% | `ProcessGroupHCCL.cpp` |
| 错误类型相同 | 30% | API 删除、签名变更、枚举重命名 |
| 关键标识符相同 | 30% | `Ascend910_95`、`SocVersion`、`IsCompatibleSoc` |

**判定规则**：相似度 ≥ 70% 视为重复 issue

### 示例场景

| 场景 | 本地标题 | 远程标题 | 判定 |
|------|----------|----------|------|
| 标题精确匹配 | `[2026-03-26-001] ProcessGroupHCCL 引用不存在的 SocVersion 枚举值` | 相同 | ✅ 重复 |
| 标题不同，内容相同 | `[2026-03-26-001] ProcessGroupHCCL 编译错误` | `ProcessGroupHCCL SocVersion 枚举值问题` | ✅ 重复（语义匹配） |
| 不同问题 | `[2026-03-26-001] ProcessGroupHCCL 枚举错误` | `CachingHostAllocator API 删除` | ❌ 不重复 |

**关键原则**：只要本地文件有 `gitcode_issue_id`，就认为已同步，不再进行任何检查。

---

## 注意事项

- **正文内容**：使用文件全部内容作为 body，包括标题行
- **标签**：所有 issue 统一添加 `ai-analyze`、`nightly-ci` 和 `bug` 三个标签
- **目标仓库**：固定为 `kerer-sk/pytorch`
- **本地文件更新**：同步成功后必须更新本地文件添加 `gitcode_issue_id`，避免重复提交

---

## 错误案例

### 案例：远程 issue 被删除后重复创建

**现象**：
1. 第一次执行 `gc issue list` 返回 `#1, #2, #3`，匹配到 `#3` 标题相同
2. 更新本地文件 frontmatter 为 `gitcode_issue_id: 3`
3. 后来远程 `#1, #2, #3` 被删除（或仓库重置）
4. 第二次执行 `gc issue list` 返回 `No issues found`
5. 错误地基于第一次的记忆，先写 `gitcode_issue_id: 3`，再创建新 issue 得到 `#4`

**正确做法**：
- 每次执行都以 `gc issue list` 的**实时结果**为准，不假设之前看到过的 issue 仍然存在
- 创建新 issue 后，以 `gc issue create` 返回的 ID 写入 frontmatter
- 若远程列表为空或无匹配，应直接创建新 issue