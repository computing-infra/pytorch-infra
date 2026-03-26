分析最新一次失败的 GitHub Actions CI 构建，自动判断失败类型并输出结构化报告。

> **注意**：本项目仅进行问题分析和建议，不直接修复代码。

---

## 前置检查

### 步骤 0：检查 GitHub CLI 登录状态

**必须先验证 gh 命令可用且已登录，否则无法获取日志。**

```bash
gh auth status
```

| 输出内容 | 状态 | 处理方式 |
|----------|------|----------|
| `Logged in to github.com` | ✅ 已登录 | 继续执行 |
| `not logged in` | ❌ 未登录 | 提示用户运行 `gh auth login` |
| `token expired` | ❌ token 过期 | 提示用户运行 `gh auth refresh` |
| `command not found` | ❌ gh 未安装 | 提示用户安装 GitHub CLI |

---

## 执行步骤

### 第一步：找到最近的失败 Run

```bash
gh run list --repo computing-infra/pytorch-infra --limit 10
```

记录最新一条 `failure` 状态的 Run ID 和触发时间。

**构建进度判断（运行时长）：**
- `< 2 分钟` → 早期失败（checkout、依赖安装、gh 登录问题）
- `2-10 分钟` → 中期失败（PyTorch 安装、代码克隆）
- `> 30 分钟` → 编译阶段失败（API 不兼容）

### 第二步：提取版本信息

```bash
# 提取 PyTorch nightly 版本
gh run view <run_id> --repo computing-infra/pytorch-infra --log 2>&1 \
  | grep -E "PyTorch nightly version:" | head -1

# 提取 Ascend/pytorch commit
gh run view <run_id> --repo computing-infra/pytorch-infra --log 2>&1 \
  | grep -E "Ascend/pytorch commit:" | head -1
```

**记录：** `torch_version`、`ascend_commit`、`ascend_commit_date`

### 第三步：拉取失败日志并判断类型

```bash
# 获取失败日志
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 | head -300

# 检查失败特征关键词
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 \
  | grep -E "error:|make\[.*\]:|Invalid format|GITHUB_OUTPUT|Permission denied|exceeded the maximum|Unable to locate|Connection refused" \
  | head -30
```

根据匹配的关键词，对照下方「已知失败类型」进行诊断。

---

## 诊断流程

### A. 编译失败

```bash
# 提取关键错误
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 \
  | grep -E "error:|fatal error|make\[|FAILED" \
  | head -50
```

**定位源文件：** 使用提取的 `ascend_commit` 切换到对应代码版本：

```bash
ASCEND_COMMIT="<从日志提取的完整 commit hash>"

if [ -d ".tmp/ascend_pytorch" ]; then
  cd .tmp/ascend_pytorch && git fetch --depth=1 origin ${ASCEND_COMMIT} && git checkout ${ASCEND_COMMIT} && cd -
else
  git clone --depth=1 --branch main https://gitcode.com/Ascend/pytorch.git .tmp/ascend_pytorch
  cd .tmp/ascend_pytorch && git fetch --depth=1 origin ${ASCEND_COMMIT} && git checkout ${ASCEND_COMMIT} && cd -
fi
```

### B. Workflow 脚本失败

```bash
# 检查输出格式错误
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 \
  | grep -E "GITHUB_OUTPUT|echo.*>>" | head -30
```

### C. 依赖安装失败

```bash
gh run view <run_id> --repo computing-infra/pytorch-infra --log-failed 2>&1 \
  | grep -E "apt-get|pip install|E:|ERROR|Could not find" \
  | head -50
```

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
| 失败类型 | <类型> |
| Action 链接 | https://github.com/computing-infra/pytorch-infra/actions/runs/<run_id> |

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
- 编译失败 → `/report-issue`
- Workflow 失败 → 直接修复 `.github/workflows/*.yml`
- 依赖/网络问题 → 检查外部服务状态
```

---

## 已知失败类型

### 一级分类（5 类）

| 类型 | 特征关键词 | 后续操作 |
|------|------------|----------|
| **编译失败** | `error:`、`make[*]:`、`fatal error` | `/report-issue` |
| **Workflow 脚本失败** | `Invalid format`、`GITHUB_OUTPUT`、`Permission denied` | 直接修复 workflow |
| **依赖安装失败** | `Unable to locate package`、`pip install failed` | 检查外部服务 |
| **超时失败** | `exceeded the maximum execution time` | 调整 timeout |
| **网络问题** | `Connection refused`、`timed out`、`Could not resolve host` | 重试或换源 |

### 编译失败二级分类（6 类）

| 子类型 | 特征日志 | 根本原因 | 修复方向 |
|--------|----------|----------|----------|
| **C1 API 删除** | `has no member named`、`is not a member of`、`undeclared identifier` | 上游删除了字段、函数、枚举值 | 查找替代 API |
| **C2 签名变更** | `marked 'override', but does not override`、`no matching function` | 函数参数或返回值变化 | 更新函数签名 |
| **C3 接口新增** | `abstract class type`、`cannot instantiate` | 基类新增纯虚函数未实现 | 补充实现 |
| **C4 头文件变更** | `file not found`、`no such file or directory` | include 路径或文件名变化 | 调整路径 |
| **C5 类型不兼容** | `cannot convert`、`no type named` | 类型定义或模板参数变化 | 适配新类型 |
| **C6 链接错误** | `undefined reference`、`cannot find -l` | 符号或库缺失 | 检查依赖 |

---

## 更新失败类型

**分析完成后，若发现新类型：**
1. 总结特征关键词和根本原因
2. 更新上方分类表格
3. 提交变更：`git add/commit/push`

**分类原则：**
- 按根本原因分类，而非错误表象
- 合并优先：相似失败合并为同一类型，避免类型膨胀

---

## 注意事项

- 若日志量大，重点看第一个 `error:` 出现的位置
- 若 wheel 已生成但 step 仍失败，优先判断为 CI 脚本问题
- 每次编译失败通常只暴露**当前最早的**错误
- 本地克隆路径：`.tmp/ascend_pytorch`
- PyTorch nightly 头文件路径：`/usr/local/lib/python3.12/dist-packages/torch/include/`