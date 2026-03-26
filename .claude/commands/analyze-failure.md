分析最新一次失败的 GitHub Actions CI 构建，自动判断失败类型并输出结构化报告。

> **注意**：本项目仅进行问题分析和建议，不直接修复代码。

---

## 前置检查

### 步骤 0：检查 GitHub CLI 登录状态

**必须先验证 gh 命令可用且已登录，否则无法获取日志。**

```bash
gh auth status
```

**判断结果：**

| 输出内容 | 状态 | 处理方式 |
|----------|------|----------|
| `Logged in to github.com` | ✅ 已登录 | 继续执行 |
| `not logged in` | ❌ 未登录 | 提示用户运行 `gh auth login` |
| `token expired` | ❌ token 过期 | 提示用户运行 `gh auth refresh` |
| `command not found` | ❌ gh 未安装 | 提示用户安装 GitHub CLI |

**如果未登录或过期，告知用户：**
```
GitHub CLI 未登录或 token 已过期，请先执行：
  gh auth login
或刷新 token：
  gh auth refresh
```

---

## 失败类型判断

执行诊断时，根据日志特征自动判断失败类型：

| 类型 | 特征关键词 | 说明 |
|------|------------|------|
| **编译失败** | `error:`、`make[*]:`、`fatal error` | C++ 编译错误，通常是 API 不兼容 |
| **Workflow 脚本失败** | `Invalid format`、`GITHUB_OUTPUT`、`Permission denied` | CI 脚本语法或配置问题 |
| **依赖安装失败** | `E: Unable to locate package`、`pip install failed` | 系统包或 Python 包安装失败 |
| **超时失败** | `exceeded the maximum execution time` | 构建时间过长 |
| **网络问题** | `Connection refused`、`timed out`、`Could not resolve host` | 网络连接问题 |

---

## 执行步骤

### 第一步：找到最近的失败 Run

```bash
gh run list --repo kerer-ai/pytorch-npu-codex --limit 10
```

记录最新一条 `failure` 状态的 Run ID 和触发时间。

**构建进度判断（运行时长）：**
- `< 2 分钟` → 早期失败（checkout、依赖安装、gh 登录问题）
- `2-10 分钟` → 中期失败（PyTorch 安装、代码克隆）
- `> 30 分钟` → 编译阶段失败（API 不兼容）

### 第二步：提取版本信息

**从构建日志中提取 PyTorch nightly 版本和 Ascend/pytorch commit id：**

```bash
# 获取完整日志（包含成功步骤）
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log 2>&1 | head -500

# 提取 PyTorch nightly 版本
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log 2>&1 \
  | grep -E "PyTorch nightly version:" | head -1

# 提取 Ascend/pytorch commit
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log 2>&1 \
  | grep -E "Ascend/pytorch commit:" | head -1
```

**输出示例：**
```
PyTorch nightly version: 2.11.0.dev20260326
Ascend/pytorch commit: abc123def456 (2026-03-25 10:00:00 +0800)
```

**记录以下信息：**
- `torch_version`：PyTorch nightly 版本号
- `ascend_commit`：Ascend/pytorch 完整 commit hash
- `ascend_commit_short`：Ascend/pytorch 短 commit hash
- `ascend_commit_date`：Ascend/pytorch commit 时间

### 第三步：拉取失败日志并判断类型

```bash
# 查看失败 Run 概览
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex

# 获取失败日志
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log-failed 2>&1 | head -300
```

**判断失败类型：**

```bash
# 检查各类失败特征
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log-failed 2>&1 \
  | grep -E "error:|make\[.*\]:|Invalid format|GITHUB_OUTPUT|Permission denied|exceeded the maximum|Unable to locate|Connection refused" \
  | head -30
```

根据匹配的关键词，选择对应的诊断流程。

---

## 诊断流程

### A. 编译失败诊断

#### A1. 提取关键错误

```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log-failed 2>&1 \
  | grep -E "error:|fatal error|make\[|FAILED" \
  | head -50
```

#### A2. 常见编译错误类型

| 错误模式 | 含义 | 常见原因 |
|----------|------|----------|
| `'struct X' has no member named 'Y'` | 结构体成员不存在 | 上游删除或重命名了字段 |
| `'Z' marked 'override', but does not override` | 虚函数签名变更 | 上游修改了函数签名 |
| `invalid new-expression of abstract class type` | 抽象类无法实例化 | 基类新增纯虚函数未实现 |
| `no matching function for call to 'X'` | 函数调用不匹配 | 函数签名变更或重载消失 |
| `use of undeclared identifier 'X'` | 标识符未声明 | 头文件路径变更或宏定义变化 |
| `'X' is not a member of 'Y'` | 枚举/命名空间成员不存在 | 枚举值被删除或重命名 |

#### A3. 定位源文件

**使用从 CI 日志中提取的 Ascend/pytorch commit id（`ASCEND_COMMIT`）切换到对应代码版本：**

```bash
# 设置目标 commit（从第二步提取）
ASCEND_COMMIT="<从日志提取的完整 commit hash>"

# 若本地源码已存在，fetch 并 checkout 到目标 commit
if [ -d ".tmp/ascend_pytorch" ]; then
  cd .tmp/ascend_pytorch
  git fetch --depth=1 origin ${ASCEND_COMMIT}
  git checkout ${ASCEND_COMMIT}
  cd -
# 若不存在，克隆指定 commit
else
  git clone --depth=1 --branch main https://gitcode.com/Ascend/pytorch.git .tmp/ascend_pytorch
  cd .tmp/ascend_pytorch
  git fetch --depth=1 origin ${ASCEND_COMMIT}
  git checkout ${ASCEND_COMMIT}
  cd -
fi

# 查看受影响文件
cat .tmp/ascend_pytorch/<受影响文件路径>
```

### B. Workflow 脚本失败诊断

#### B1. 输出格式错误

**特征：**
```
Unable to process file command 'output'
Invalid format
```

**常见原因：**
- 多行文本直接写入 `$GITHUB_OUTPUT`
- 输出值包含特殊字符（`}`、`|`、换行）

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log-failed 2>&1 \
  | grep -E "GITHUB_OUTPUT|echo.*>>" | head -30
```

#### B2. 权限问题

**特征：**
```
Permission denied
Error: Resource not accessible by integration
```

**检查方法：** 查看 workflow 中的 `permissions` 配置

#### B3. 表达式错误

**特征：**
```
Unrecognized named-value: 'xxx'
The expression is not valid
```

**检查方法：**
```bash
grep -n "\${{" .github/workflows/nightly-build.yml
```

### C. 依赖安装失败诊断

**特征：**
```
E: Unable to locate package
pip install failed
ERROR: Could not find a version
```

**检查方法：**
```bash
gh run view <run_id> --repo kerer-ai/pytorch-npu-codex --log-failed 2>&1 \
  | grep -E "apt-get|pip install|E:|ERROR|Could not find" \
  | head -50
```

### D. 超时失败诊断

**特征：**
```
The job running on runner ... has exceeded the maximum execution time
```

**分析要点：**
- 检查是否有无限循环或死锁
- 检查编译并行数是否合理
- 考虑增加 `timeout-minutes`

---

## 输出报告模板

```
## CI 失败分析报告

### 构建信息
| 项目 | 详情 |
|------|------|
| Run ID | `<run_id>` |
| 触发时间 | YYYY-MM-DD HH:MM UTC |
| 运行时长 | XX 分钟 |
| 失败类型 | 编译失败 / Workflow 脚本失败 / 依赖安装失败 / 超时 |
| Action 链接 | https://github.com/kerer-ai/pytorch-npu-codex/actions/runs/<run_id> |

### 版本信息
| 项目 | 详情 |
|------|------|
| PyTorch Nightly | `2.11.0.dev20260326` |
| Ascend/pytorch Commit | `abc123def456` (2026-03-25) |
| Commit 链接 | https://gitcode.com/Ascend/pytorch/commit/abc123def456 |

### 失败 Step
- Step 名称：`<step_name>`
- 失败原因概述：

### 错误摘要
```
<关键错误日志原文，3-5 条>
```

### 根本原因
（说明是什么导致了失败）

### 受影响范围
- 文件：`<相对路径>`
- 涉及类/函数：

### 建议修复方向
1. 具体建议
2. 注意事项

### 后续操作
- 编译失败 → `/report-issue` 创建 issue 文档
- Workflow 失败 → 直接修改 `.github/workflows/*.yml`
```

---

## 常见失败类型速查表

### 编译失败

| 错误类型 | 典型日志 | 建议方向 |
|----------|----------|----------|
| API 删除 | `has no member named` | 查找替代 API 或更新调用方式 |
| 签名变更 | `marked 'override', but does not override` | 更新函数签名匹配上游 |
| 新增纯虚函数 | `abstract class type` | 实现缺失的虚函数 |
| 枚举值删除 | `is not a member of` | 使用新枚举值或添加映射 |

### Workflow 失败

| 问题类型 | 典型日志 | 建议方向 |
|----------|----------|----------|
| 多行输出 | `Invalid format` | 使用 heredoc 格式 |
| 权限不足 | `Permission denied` | 添加 `permissions` 块 |
| 表达式错误 | `Unrecognized named-value` | 检查变量拼写和作用域 |
| 缓存失败 | `Unable to restore cache` | 调整缓存 key 格式 |

### 环境/网络失败

| 问题类型 | 典型日志 | 建议方向 |
|----------|----------|----------|
| 包不存在 | `Unable to locate package` | 检查包名或换源 |
| 网络超时 | `Connection timed out` | 重试或使用镜像 |
| 磁盘满 | `No space left on device` | 清理或扩容 |

---

## 后续操作指引

| 失败类型 | 后续操作 |
|----------|----------|
| **编译失败** | 运行 `/report-issue` 创建 issue 文档 |
| **Workflow 脚本失败** | 直接修复 `.github/workflows/*.yml` |
| **依赖/网络问题** | 检查外部服务状态，必要时重试 |

---

## 注意事项

- 若日志量大（> 40 KB），`grep` 过滤后重点看第一个 `error:` 出现的位置
- 若日志显示 wheel 已成功生成，但 step 仍失败，优先判断为 CI 脚本问题
- 每次编译失败通常只暴露**当前最早的**错误，修完一个后下次构建才会暴露下一个
- 本地克隆路径：`.tmp/ascend_pytorch`
- PyTorch nightly 头文件路径：`/usr/local/lib/python3.12/dist-packages/torch/include/`

---

## 最后一步：更新常见失败类型

**分析完成后，检查本次失败是否属于已知类型，若为新类型则更新本文档。**

---

### 当前已知失败类型

**一级分类（共 5 类）：**

| 序号 | 类型 | 特征关键词 |
|------|------|------------|
| 1 | 编译失败 | `error:`、`make[*]:`、`fatal error` |
| 2 | Workflow 脚本失败 | `Invalid format`、`GITHUB_OUTPUT`、`Permission denied` |
| 3 | 依赖安装失败 | `Unable to locate package`、`pip install failed` |
| 4 | 超时失败 | `exceeded the maximum execution time` |
| 5 | 网络问题 | `Connection refused`、`timed out`、`Could not resolve host` |

**编译失败二级分类（共 6 类）：**

| 序号 | 子类型 | 特征日志 | 根本原因 |
|------|--------|----------|----------|
| C1 | **API 删除** | `has no member named`、`is not a member of`、`undeclared identifier` | 上游删除了字段、函数、枚举值 |
| C2 | **签名变更** | `marked 'override', but does not override`、`no matching function` | 函数参数类型或返回值变化 |
| C3 | **接口新增** | `abstract class type`、`cannot instantiate` | 基类新增纯虚函数未实现 |
| C4 | **头文件变更** | `file not found`、`no such file or directory` | include 路径或文件名变化 |
| C5 | **类型不兼容** | `cannot convert`、`no type named` | 类型定义或模板参数变化 |
| C6 | **链接错误** | `undefined reference`、`cannot find -l` | 符号或库缺失 |

---

### 判断与更新流程

1. **匹配一级分类**：根据特征关键词判断大类
2. **编译失败需匹配二级分类**：进一步定位具体原因
3. **发现新类型**：若均不匹配，总结特征和根本原因
4. **更新文档**：将新类型加入对应分类表格
5. **提交变更**：执行 `git add/commit/push` 同步

---

### 分类原则

- **按根本原因分类**：而非错误表象
- **一级分类 ≤ 5 类**：编译、Workflow、依赖、超时、网络
- **编译二级分类 ≤ 6 类**：API 删除、签名变更、接口新增、头文件、类型、链接
- **合并优先**：相似失败合并为同一类型，避免类型膨胀

---

### 编译失败分类速查

```
编译失败
├─ C1 API 删除    → 成员/函数/枚举被移除 → 查找替代或适配
├─ C2 签名变更    → 函数参数/返回值变化 → 更新调用方式
├─ C3 接口新增    → 新纯虚函数未实现    → 补充实现
├─ C4 头文件变更  → include 路径变化     → 调整路径
├─ C5 类型不兼容  → 类型定义变化         → 适配新类型
└─ C6 链接错误    → 符号/库缺失          → 检查依赖
```