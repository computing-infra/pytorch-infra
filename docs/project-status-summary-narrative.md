# PyTorch Infra 项目方案与阶段进展总结

## 1. 项目背景

`Ascend/pytorch` 需要持续跟踪 PyTorch 主社区 nightly 演进，及时发现接口变更、构建兼容性问题和 NPU 运行时问题。

本项目的建设目标，是围绕 `Ascend/pytorch` 建立一套持续验证平台，覆盖以下三类核心能力：

1. 验证 `Ascend/pytorch` 与 PyTorch nightly 的集成构建是否持续兼容。
2. 在昇腾 NPU 环境中运行 PyTorch 主社区测试用例，发现设备适配与运行时问题。
3. 对失败结果进行归因分析，沉淀 issue，并推动问题反馈和修复到 `Ascend/pytorch` 上游。

从定位上看，本项目不是业务服务仓库，而是一个面向 `Ascend/pytorch` 的“兼容性验证平台 + NPU 测试平台 + 问题闭环平台”。

## 2. 项目目标

项目目标建议分为三层：

### 2.1 Nightly 集成构建验证

通过 GitHub Actions 每日自动拉取 PyTorch nightly，集成构建 `Ascend/pytorch`，识别以下问题：

- PyTorch API 删除或重命名
- 函数签名变化
- 类型定义变化
- 头文件路径变化
- 构建依赖和工具链变化

### 2.2 昇腾 NPU 真机验证

在真实 NPU 环境中执行 `torch_npu` 的构建、安装和基础测试，验证以下能力：

- `torch_npu` 是否能成功安装
- CANN / NNAL 环境是否可正确加载
- NPU 设备是否可识别、可初始化
- 基础设备测试是否通过

### 2.3 问题分析与上游闭环

对 nightly 构建失败和 NPU 测试失败自动进行分类和总结，输出：

- 失败阶段
- 关键错误日志
- 受影响文件/模块
- 初步修复建议
- GitHub issue / GitCode issue

最终形成“发现问题 -> 总结问题 -> 提交 issue -> 推动上游修复”的闭环。

## 3. 总体方案设计

项目当前方案可分为四个子系统。

### 3.1 子系统 A：Nightly 构建验证

负责每日对 `Ascend/pytorch` 与 PyTorch nightly 的集成构建兼容性进行验证。

当前落地 workflow：

- [nightly-build.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/nightly-build.yml)
- [nightly-build-arm.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/nightly-build-arm.yml)

覆盖场景：

- x86 环境 nightly 构建
- ARM 自托管 NPU runner nightly 构建

构建成功后上传 wheel 和 build log，构建失败时保留日志用于分析。

### 3.2 子系统 B：昇腾 NPU 构建与测试

负责在真实昇腾 NPU 环境中完成：

1. 构建 `torch_npu`
2. 安装 wheel
3. 加载 CANN 环境
4. 验证 NPU 可用性
5. 执行基础测试

当前落地 workflow：

- [npu-test.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/npu-test.yml)

当前流程已从“下载已有 wheel 再测试”演进为“构建 -> 安装 -> 测试”的一体化模式。

### 3.3 子系统 C：静态扫描与规则治理

负责对 `Ascend/pytorch` 做静态代码检查，尽可能在构建前发现低成本问题。

当前落地 workflow 和配置：

- [lint.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/lint.yml)
- [\_lint.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/_lint.yml)
- [lint-config/.lintrunner.toml](/home/wpf/claude-code/pta/pytorch-infra/lint-config/.lintrunner.toml)

当前已迁移多类规则，包括：

- CLANGFORMAT
- RUFF
- CODESPELL
- SHELLCHECK
- ACTIONLINT
- CMAKE
- PYPROJECT
- CMAKE_MINIMUM_REQUIRED

### 3.4 子系统 D：失败分析与 issue 闭环

负责对 workflow 失败进行自动化分析、总结和问题流转。

当前实现材料：

- [analyze-failure.md](/home/wpf/claude-code/pta/pytorch-infra/.claude/commands/analyze-failure.md)
- [sync-issues.md](/home/wpf/claude-code/pta/pytorch-infra/.claude/commands/sync-issues.md)
- [ci-analysis-report.md](/home/wpf/claude-code/pta/pytorch-infra/report/ci-analysis-report.md)

该子系统目标是把 nightly 失败从“日志堆积”转成“可追踪问题单”。

## 4. 当前落地进展

本节结合仓库现状和 `2026-04-03` 使用 `gh` 命令查询到的 GitHub Actions 数据进行说明。

### 4.1 Workflow 实际运行统计

通过以下命令对最近 200 次 run 做了聚合统计：

```bash
gh run list --repo computing-infra/pytorch-infra --limit 200 --json workflowName,conclusion,createdAt
```

统计结果如下：

| Workflow | 总计 | 成功 | 失败 | 取消 |
|----------|------|------|------|------|
| Ascend/pytorch Nightly Build Validation | 25 | 24 | 1 | 0 |
| Ascend/pytorch Nightly Build Validation (ARM) | 20 | 8 | 12 | 0 |
| NPU Build and Test | 29 | 2 | 25 | 2 |
| Lint Ascend/pytorch | 28 | 22 | 6 | 0 |

### 4.2 当前成熟度判断

从实际运行数据看，当前项目各能力成熟度如下：

| 能力方向 | 当前状态 | 判断 |
|----------|----------|------|
| x86 nightly 构建验证 | 已稳定运行 | 成熟度高 |
| ARM nightly 构建验证 | 已跑通，但依赖自托管 runner 稳定性 | 成熟度中 |
| NPU build-and-test | 已首次成功，整体仍在打磨期 | 成熟度中低 |
| 静态扫描与问题治理 | 已落地并可运行 | 成熟度中高 |

### 4.3 最近成功记录

通过 `gh run list` 查询最近成功记录，结果如下：

| Workflow | 最近成功时间 (UTC) | Run ID | 链接 |
|----------|--------------------|--------|------|
| NPU Build and Test | 2026-04-02 23:38:48 | 23927010611 | https://github.com/computing-infra/pytorch-infra/actions/runs/23927010611 |
| Ascend/pytorch Nightly Build Validation | 2026-04-02 22:23:56 | 23924812258 | https://github.com/computing-infra/pytorch-infra/actions/runs/23924812258 |
| Ascend/pytorch Nightly Build Validation (ARM) | 2026-04-02 09:10:38 | 23893095476 | https://github.com/computing-infra/pytorch-infra/actions/runs/23893095476 |
| Lint Ascend/pytorch | 2026-04-01 01:13:31 | 23827086198 | https://github.com/computing-infra/pytorch-infra/actions/runs/23827086198 |

其中最关键的进展有两点：

1. `x86 nightly` 已经连续稳定运行，说明主链路已具备日常兼容性监测能力。
2. `NPU Build and Test` 已在 `2026-04-02` 成功执行，说明昇腾 NPU 构建和基础测试链路已完成首次跑通。

## 5. 分阶段建设成果

### 5.1 第一阶段成果：Nightly 构建兼容性验证能力已建立

项目已具备每日自动验证 `Ascend/pytorch` 与 PyTorch nightly 编译兼容性的能力。

当前成果包括：

- x86 nightly 构建 workflow 已稳定运行
- ARM nightly 构建 workflow 已跑通
- 支持 wheel / build log artifact 上传
- 支持手动指定 nightly 日期触发
- 支持 pip 缓存与 ccache 加速

该阶段已经证明项目具备“主社区 nightly 演进雷达”的能力。

### 5.2 第二阶段成果：昇腾 NPU 测试链路已从方案走向可运行

NPU workflow 近期经历了集中调试，目前已取得阶段性成果：

- 完成 NPU 自托管 runner + 容器方案落地
- 完成 `torch_npu` 构建、安装、环境加载测试
- 完成基础 NPU 可用性验证链路搭建
- 已产生至少 1 次成功 run

这意味着项目已从“仅验证能否编译”迈向“验证是否能在昇腾设备上运行”。

### 5.3 第三阶段成果：静态扫描和问题治理体系已形成

当前 lint 体系已不是单一格式化检查，而是一个对 `Ascend/pytorch` 进行规则治理的平台。

阶段成果包括：

- 已迁移 20+ lint 规则
- 已实现 lint report 生成和 artifact 上传
- 已具备 issue 分析、去重、同步上游的工作流基础

这部分能力将进一步降低问题排查成本，并补充构建验证盲区。

## 6. 当前发现的主要问题

### 6.1 ARM nightly 当前主要瓶颈：runner 资源稳定性

最近一次 ARM nightly 失败 Run：

- Run ID: `23924845622`
- 时间: `2026-04-02 22:24:55 UTC`

通过 `gh run view 23924845622 --repo computing-infra/pytorch-infra` 查询到的关键失败信息：

```text
The job was not acquired by Runner of type self-hosted even after multiple attempts
```

这说明当前 ARM 方向最近的主要问题已经不是编译逻辑本身，而是：

- self-hosted runner 可用性
- runner 调度稳定性
- runner 资源供给与接单能力

### 6.2 NPU 当前主要瓶颈：设备环境与运行时初始化

一个代表性失败 Run：

- Run ID: `23876199231`
- 时间: `2026-04-01 23:39:38 UTC`

通过 `gh run view 23876199231 --repo computing-infra/pytorch-infra` 查询，失败发生在：

- `Verify NPU availability`

而不是失败在正式社区测试阶段。

这说明当前 NPU 方向的核心问题仍然集中在基础环境层，包括：

- CANN 环境变量加载
- 挂载路径一致性
- 容器内 Ascend 路径识别
- `torch_npu` 导入与 NPU 初始化

因此当前 NPU 方向的首要任务仍然是打稳环境，不宜过早追求大规模社区测试覆盖。

### 6.3 Lint 和 issue 治理方向仍需强化自动化闭环

虽然 lint 和 issue 体系已具备基础能力，但从项目整体看，后续仍可继续增强：

- 自动判断 issue 是否已修复
- 自动区分环境失败和代码兼容性失败
- 自动生成周报 / 月报
- 自动同步 GitHub issue 到 `Ascend/pytorch` 上游

## 7. 关键结论

### 7.1 项目已经完成从“方案设计”到“运行平台”的跨越

截至 `2026-04-03`，本项目已经不再是单纯的设计方案，而是一套正在持续输出验证结果的自动化平台。

已经确认落地的能力包括：

- x86 nightly 集成构建验证
- ARM nightly 集成构建验证
- 昇腾 NPU build-and-test 初步验证
- 静态扫描治理
- issue 分析与问题沉淀

### 7.2 当前最成熟成果是 x86 nightly 验证链路

从最近 200 次 run 的统计看，x86 workflow：

- 总计 `25` 次
- 成功 `24` 次
- 失败 `1` 次

说明这部分已具备较高稳定性，能够承担主社区 nightly 兼容性监控职责。

### 7.3 当前最值得继续投入的是 ARM / NPU 稳定性建设

ARM 和 NPU 的主要问题已经逐渐从“流程设计是否正确”转向“环境是否稳定可用”。

后续最优先的工作应聚焦：

1. 提升 self-hosted runner 的稳定性和可调度性
2. 固化 NPU 容器镜像和环境变量加载方式
3. 稳定 NPU 基础 smoke 测试
4. 再逐步扩大 PyTorch 主社区测试用例覆盖

### 7.4 项目已经体现出对上游的真实价值

项目价值不只是“某次构建成功”，而是通过 nightly 和 NPU 验证持续发现问题，并将问题结构化沉淀和反馈给 `Ascend/pytorch`。

从已有报告和 issue 记录可以看出，项目已经在以下方面发挥作用：

- 提前暴露 PyTorch nightly 演进带来的兼容性问题
- 识别 `Ascend/pytorch` 的接口适配滞后问题
- 为上游修复提供稳定的证据链和 issue 输入

## 8. 下一阶段计划建议

建议下一阶段重点推进以下工作：

### 8.1 稳定基础设施

- 提升 self-hosted ARM/NPU runner 的可用性
- 建立 runner 健康检查与告警机制
- 固化稳定镜像版本和挂载配置

### 8.2 稳定 NPU 基础验证

- 固化 NPU availability 检查逻辑
- 优先维护 smoke 用例集合
- 建立最小可回归测试池

### 8.3 扩展 PyTorch 主社区测试覆盖

- 从 `test_device.py` 扩展到核心 tensor / autograd / nn 基础测试
- 建立 smoke / core / extended 三层测试池
- 建立 disable list 与错误分类清单

### 8.4 增强问题自动闭环

- 自动生成失败归因报告
- 自动创建 / 更新 issue
- 自动同步 GitHub issue 到 `Ascend/pytorch`
- 自动输出周报 / 月报，沉淀项目成效指标

## 9. 汇报口径建议

对外汇报时，可以将项目当前状态概括为：

> 本项目已初步建成面向 `Ascend/pytorch` 的持续验证平台，已稳定具备 x86 nightly 集成构建验证能力，ARM nightly 构建已跑通，昇腾 NPU 构建与基础测试链路已首次成功执行。当前工作重点正从“流程打通”转向“环境稳定化和主社区测试覆盖扩展”，项目已能够持续发现兼容性问题并推动上游修复。
