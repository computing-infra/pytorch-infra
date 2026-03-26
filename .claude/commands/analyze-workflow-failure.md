分析 GitHub Actions workflow 脚本层面的失败问题，定位并给出修复建议。

## 失败类型判断

先区分失败类型：

| 类型 | 特征 | 处理方式 |
|------|------|----------|
| **编译失败** | `error:`、`make[*]:`、C++ 错误 | 使用 `/analyze-failure` |
| **Workflow 脚本失败** | `Invalid format`、`GITHUB_OUTPUT`、权限、超时 | 继续执行本 skill |

## 执行步骤

### 第一步：获取失败 Run 信息

```bash
gh run list --repo kerer-ai/pytorch-npu --limit 5
```

记录最新失败 Run 的 ID，然后获取失败步骤：

```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu
```

### 第二步：拉取失败日志

```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 | head -200
```

### 第三步：分类诊断

#### 3.1 输出格式错误

**特征：**
```
Unable to process file command 'output'
Invalid format
```

**常见原因：**
- 多行文本直接写入 `$GITHUB_OUTPUT`
- 输出值包含特殊字符（如 `}`、`|`）

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "GITHUB_OUTPUT|echo.*>>" \
  | head -30
```

**修复建议：**
- 使用 heredoc 格式输出多行：`name<<EOF ... EOF`
- 或只输出单行值

#### 3.2 表达式错误

**特征：**
```
Unrecognized named-value: 'xxx'
Property 'xxx' is required
The expression is not valid
```

**常见原因：**
- 拼写错误（如 `steps.build.outputs.status` 写错）
- 引用不存在的 output 或环境变量
- 类型不匹配（如字符串与数字比较）

**检查方法：**
查看 workflow 文件中的表达式：
```bash
grep -n "\${{" .github/workflows/nightly-build.yml
```

#### 3.3 权限问题

**特征：**
```
Permission denied
Error: Resource not accessible by integration
```

**常见原因：**
- `GITHUB_TOKEN` 权限不足
- 需要在 workflow 中添加 `permissions` 块

**修复建议：**
```yaml
permissions:
  contents: read
  actions: write
```

#### 3.4 超时

**特征：**
```
The job running on runner ... has exceeded the maximum execution time
```

**修复建议：**
- 增加超时时间：`timeout-minutes: 120`
- 或优化构建步骤

#### 3.5 依赖安装失败

**特征：**
```
E: Unable to locate package
pip install failed
```

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "apt-get|pip install|E:|ERROR" \
  | head -50
```

#### 3.6 缓存问题

**特征：**
```
Unable to restore cache
Cache save failed
```

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "cache|Cache|ccache" \
  | head -30
```

#### 3.7 Artifact 问题

**特征：**
```
Unable to upload artifact
No files were found
```

**常见原因：**
- 文件路径错误
- 构建未生成预期文件

### 第四步：输出诊断报告

```
## Workflow 失败诊断报告

### 失败 Run 信息
- Run ID：
- 失败 Step：
- 触发时间：

### 错误类型
（输出格式错误 / 表达式错误 / 权限问题 / 超时 / 依赖安装 / 缓存 / Artifact）

### 错误摘要
（关键错误日志原文）

### 根本原因
（说明 workflow 中哪个配置或写法导致失败）

### 修复建议
1. 具体修改点（文件:行号）
2. 修改内容

### 相关文件
- `.github/workflows/nightly-build.yml` 第 X 行
```

## 常见修复模式

| 问题 | 修复方式 |
|------|----------|
| 多行写入 GITHUB_OUTPUT | 改用 heredoc 或输出单行 |
| 引用不存在的 output | 检查 step id 和 output 名称拼写 |
| 权限不足 | 添加 `permissions` 块 |
| 缓存 key 冲突 | 调整 key 格式，加入日期或 run_id |
| 路径不存在 | 检查相对路径，使用 `ls` 调试 |

## 注意事项

- 若日志显示 wheel 构建成功但 step 失败，优先排查脚本问题
- 修改 workflow 后，建议手动触发验证
- workflow 语法问题通常不需要创建 issue 文档，直接修复即可