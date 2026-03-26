分析最新一次失败的 GitHub Actions CI 构建，自动判断失败类型并输出结构化报告。

## 失败类型判断

执行诊断时，根据日志特征自动判断失败类型：

| 类型 | 特征 | 诊断流程 |
|------|------|----------|
| **编译失败** | `error:`、`make[*]:`、C++ 错误 | → 编译诊断流程 |
| **Workflow 脚本失败** | `Invalid format`、`GITHUB_OUTPUT`、权限、超时 | → Workflow 诊断流程 |

---

## 执行步骤

### 第一步：找到最近的失败 Run

```bash
gh run list --repo kerer-ai/pytorch-npu --limit 5
```

记录最新一条 `failure` 状态的 Run ID 和触发时间。同时观察**构建进度**（运行时长）：
- 时长很短（< 5 分钟）→ 失败在早期步骤（依赖安装、workflow 语法等）
- 时长较长（> 30 分钟）→ 编译阶段失败，说明前序步骤均已通过

### 第二步：拉取失败日志并判断类型

```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 | head -200
```

**判断失败类型：**

```bash
# 检查是否为 workflow 脚本问题
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "Unable to process file command|Invalid format|GITHUB_OUTPUT|Permission denied|exceeded the maximum" \
  | head -20
```

- **有匹配** → Workflow 脚本失败，执行 [Workflow 诊断流程](#workflow-诊断流程)
- **无匹配** → 编译失败，执行 [编译诊断流程](#编译诊断流程)

---

## 编译诊断流程

### C1. 过滤关键错误行

```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "error:|Error|FAILED|fatal|Traceback|make\[|Applying patch|✅|❌" \
  | head -100
```

重点关注：
- `make[2]: *** [...] Error 1` → 定位到具体编译失败的 `.cpp` 文件
- `error: 'struct X' has no member named 'Y'` → 结构体成员被上游删除或重命名
- `error: 'Z' marked 'override', but does not override` → 虚函数签名变更
- `error: invalid new-expression of abstract class type` → 基类新增纯虚函数未实现
- `✅ OK` / `❌ FAILED` → 哪些 patch 成功打入，哪些失败

### C2. 定位受影响源文件，对比新旧 API

确认失败的 `.cpp` / `.hpp` 文件后，读取对应源码：

```bash
# 读取 Ascend/pytorch 源文件（使用本地克隆）
cat /root/ascend_pytorch_tmp/<受影响文件路径>
```

然后在 PyTorch nightly 安装的头文件中查找对应的新 API：

```bash
TORCH_INCLUDE=$(python3 -c "import torch,os; print(os.path.dirname(torch.__file__))")/include
# 按关键词搜索相关头文件
grep -rn "<变更的类名或函数名>" $TORCH_INCLUDE --include="*.h" | head -20
# 读取具体头文件
cat $TORCH_INCLUDE/<相关头文件路径>
```

### C3. 输出编译诊断报告

```
## 失败 Run 信息
- Run ID：
- 触发时间：
- 失败类型：编译失败
- 构建进度：（已通过 patch 数量 / 失败所在阶段）

## 已生效的 Patch
（列出 ✅ OK 的 patch，说明本次构建在哪些修复的基础上推进）

## 错误摘要
（3-5 条最关键的编译错误原文）

## 根本原因
（说明是哪个 PyTorch 上游 API 变化导致失败：结构体字段删除 / 函数签名变更 / 新增纯虚函数 等）

## 受影响范围
- 文件：（相对于 Ascend/pytorch 根目录的路径）
- 涉及类/函数：

## 建议修复方向
（最小改动原则：如何调整 Ascend 侧代码适配新 API）
```

---

## Workflow 诊断流程

### W1. 确定失败步骤

```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu
```

### W2. 分类诊断

#### W2.1 输出格式错误

**特征：**
```
Unable to process file command 'output'
Invalid format
```

**常见原因：**
- 多行文本直接写入 `$GITHUB_OUTPUT`
- 输出值包含特殊字符

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "GITHUB_OUTPUT|echo.*>>" \
  | head -30
```

**修复建议：** 使用 heredoc 格式输出多行，或只输出单行值

#### W2.2 表达式错误

**特征：**
```
Unrecognized named-value: 'xxx'
Property 'xxx' is required
The expression is not valid
```

**检查方法：** 查看 workflow 文件中的表达式
```bash
grep -n "\${{" .github/workflows/nightly-build.yml
```

#### W2.3 权限问题

**特征：**
```
Permission denied
Error: Resource not accessible by integration
```

**修复建议：** 添加 `permissions` 块
```yaml
permissions:
  contents: read
  actions: write
```

#### W2.4 超时

**特征：**
```
The job running on runner ... has exceeded the maximum execution time
```

**修复建议：** 增加超时时间或优化构建步骤

#### W2.5 依赖安装失败

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

#### W2.6 缓存/Artifact 问题

**特征：**
```
Unable to restore cache
Cache save failed
Unable to upload artifact
No files were found
```

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu --log-failed 2>&1 \
  | grep -E "cache|Cache|ccache|artifact" \
  | head -30
```

### W3. 输出 Workflow 诊断报告

```
## 失败 Run 信息
- Run ID：
- 失败 Step：
- 触发时间：
- 失败类型：Workflow 脚本失败

## 错误类型
（输出格式错误 / 表达式错误 / 权限问题 / 超时 / 依赖安装 / 缓存 / Artifact）

## 错误摘要
（关键错误日志原文）

## 根本原因
（说明 workflow 中哪个配置或写法导致失败）

## 修复建议
1. 具体修改点（文件:行号）
2. 修改内容

## 相关文件
- `.github/workflows/nightly-build.yml` 第 X 行
```

---

## 常见修复模式

| 问题类型 | 修复方式 |
|----------|----------|
| 多行写入 GITHUB_OUTPUT | 改用 heredoc 或输出单行 |
| 引用不存在的 output | 检查 step id 和 output 名称拼写 |
| 权限不足 | 添加 `permissions` 块 |
| 缓存 key 冲突 | 调整 key 格式，加入日期或 run_id |
| 路径不存在 | 检查相对路径，使用 `ls` 调试 |

---

## 后续操作指引

根据失败类型，建议后续操作：

| 失败类型 | 后续操作 |
|----------|----------|
| **编译失败** | 运行 `/report-issue` 创建 issue 文档 |
| **Workflow 脚本失败** | 直接修复 `.github/workflows/*.yml`，通常不需要创建 issue |

---

## 注意事项

- 若日志量大（> 40 KB），`grep` 过滤后重点看 `make[2]` 和第一个 `error:` 出现的位置
- 若日志显示 wheel 已成功生成，但 step 仍失败，优先判断为 CI 脚本问题
- 每次编译失败通常只暴露**当前最早的**错误，修完一个后下次构建才会暴露下一个
- 本地克隆路径：`/root/ascend_pytorch_tmp`
- PyTorch nightly 头文件路径：`/usr/local/lib/python3.12/dist-packages/torch/include/`