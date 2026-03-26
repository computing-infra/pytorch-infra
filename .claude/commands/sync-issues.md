将 GitHub 仓库的 issue 同步到 GitCode 平台（`kerer-sk/pytorch` 仓库）。

---

## 前置检查

### 检查 GitCode CLI 登录状态

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

### 第一步：获取 GitHub issue 列表

```bash
gh issue list -R computing-infra/pytorch-infra --limit 50
```

解析输出，提取每个 issue 的 ID、标题、状态、URL。

---

### 第二步：获取 GitCode issue 列表

```bash
gc issue list -R kerer-sk/pytorch --limit 100
```

解析输出，用于去重检查。

---

### 第三步：逐个同步 issue

对每个 GitHub issue 执行：

#### 3.1 检查是否已同步

读取 GitHub issue body，检查是否包含标记：

```
GitCode: https://gitcode.com/kerer-sk/pytorch/issues/123
```

- **已包含 GitCode 链接**：跳过
- **无此标记**：准备创建

#### 3.2 检查 GitCode 是否已存在相同 issue

**语义匹配检查项：**

1. **标题匹配**：标题相同或高度相似
2. **受影响文件**：对比「受影响文件」字段
3. **关键标识符**：对比类名、函数名、API 名称

**匹配规则：**
- 标题精确匹配 → 认定为重复
- 受影响文件 + 错误类型相同 → 认定为重复

#### 3.3 创建 GitCode issue

```bash
gc issue create -R kerer-sk/pytorch \
  --title "<title>" \
  --body "$(cat <<'EOF'
<GitHub issue body>

---
同步自: https://github.com/computing-infra/pytorch-infra/issues/<gh_issue_id>
EOF
)"
```

#### 3.4 添加标签

```bash
gc issue label <issue_number> --add ai-analyze,nightly-ci,bug -R kerer-sk/pytorch
```

#### 3.5 更新 GitHub issue

在 GitHub issue body 末尾添加 GitCode 链接：

```bash
gh issue edit <gh_issue_id> -R computing-infra/pytorch-infra \
  --body "$(cat <<'EOF'
<原有内容>

---
GitCode: https://gitcode.com/kerer-sk/pytorch/issues/<gitcode_issue_id>
EOF
)"
```

---

### 第四步：输出同步结果

```
## 同步结果

- 新建: X 个
- 已同步: Y 个
- 跳过（GitCode 已存在）: Z 个

### 新建 issues
- GH #123 → GitCode #456
  https://gitcode.com/kerer-sk/pytorch/issues/456
```

---

## 去重机制

| 优先级 | 检查点 | 条件 | 操作 |
|--------|--------|------|------|
| 1 | GitHub issue body | 包含 GitCode 链接 | 跳过 |
| 2 | 标题精确匹配 | 标题相同 | 跳过，更新 GitHub issue |
| 3 | 语义相似度 | 受影响文件 + 错误类型相同 | 跳过 |
| 4 | 都不满足 | — | 创建新 issue |

---

## 注意事项

- 单向同步：GitHub → GitCode
- 同步后在 GitHub issue 中添加 GitCode 链接标记
- 所有 GitCode issue 添加 `ai-analyze`、`nightly-ci`、`bug` 标签