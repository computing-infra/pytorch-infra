# PyTorch Infra 项目方案与阶段进展总结

## 1. 项目定位

| 项目项 | 内容 |
|--------|------|
| 项目名称 | PyTorch Infra 持续验证平台 |
| 服务对象 | `Ascend/pytorch` |
| 核心目标 | 持续验证 `Ascend/pytorch` 与 PyTorch nightly 的集成构建，以及在昇腾 NPU 上运行 PyTorch 主社区测试用例 |
| 价值定位 | 兼容性验证平台 + NPU 测试平台 + 问题闭环平台 |
| 输出结果 | 构建结果、测试结果、失败分析、issue、阶段报告 |

## 2. 项目总体方案

| 专项任务 | 目标 | 实现方式 | 主要载体 |
|----------|------|----------|----------|
| x86 Nightly 构建验证 | 验证 `Ascend/pytorch` 与 PyTorch nightly 的主链路编译兼容性 | GitHub Actions 定时触发，自动安装 nightly 并构建 wheel | [nightly-build.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/nightly-build.yml) |
| ARM Nightly 构建验证 | 验证 ARM / 昇腾环境下的构建兼容性 | self-hosted runner + 容器构建 | [nightly-build-arm.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/nightly-build-arm.yml) |
| 昇腾 NPU 构建与测试 | 验证 `torch_npu` 在真实 NPU 环境中的安装、初始化和基础测试能力 | 构建 wheel -> 安装 -> 加载 CANN -> 测试 | [npu-test.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/npu-test.yml) |
| 静态扫描治理 | 前置发现代码格式、规则和工程规范问题 | `lintrunner + adapters` | [lint.yml](/home/wpf/claude-code/pta/pytorch-infra/.github/workflows/lint.yml) |
| 失败分析与问题闭环 | 对失败进行归因，沉淀 issue，并推动上游修复 | Claude 命令 + issue 同步机制 | [.claude/commands/analyze-failure.md](/home/wpf/claude-code/pta/pytorch-infra/.claude/commands/analyze-failure.md) |

## 3. 专项任务进展总表

| 专项任务 | 当前进展 | 状态 | 关键说明 |
|----------|----------|------|----------|
| x86 Nightly 构建验证 | 已稳定运行，形成每日兼容性验证主链路 | 已完成 | 最近 200 次统计中成功率最高，已可作为主社区 nightly 兼容性雷达 |
| ARM Nightly 构建验证 | 已完成 workflow 落地并多次成功运行 | 持续优化中 | 已跑通，但仍依赖 self-hosted runner 稳定性 |
| 昇腾 NPU 构建与测试 | 已完成一体化流程改造，并已出现成功 run | 持续优化中 | 当前已跑通“构建 -> 安装 -> NPU 可用性验证 -> 基础测试”主流程 |
| PyTorch 主社区测试迁移 | 已完成测试框架、设备适配和迁移机制分析 | 方案完成，分批落地中 | 当前仍以基础 smoke 用例和设备验证为主，尚未大规模铺开 |
| 静态扫描治理 | 已迁移 20+ lint 规则，并具备报告输出能力 | 已完成 | 已具备 lint report 和规则治理基础能力 |
| issue 分析与同步上游 | 已形成失败分析、issue 去重、同步 GitCode 的流程设计 | 部分完成 | 流程和文档已具备，仍可继续增强自动化闭环程度 |

## 4. Workflow 运行数据汇总

### 4.1 最近 200 次运行统计

| Workflow | 总计 | 成功 | 失败 | 取消 | 结论 |
|----------|------|------|------|------|------|
| Ascend/pytorch Nightly Build Validation | 25 | 24 | 1 | 0 | 主链路稳定 |
| Ascend/pytorch Nightly Build Validation (ARM) | 20 | 8 | 12 | 0 | 已跑通，仍需稳态优化 |
| NPU Build and Test | 29 | 2 | 25 | 2 | 已打通，仍处于密集调试期 |
| Lint Ascend/pytorch | 28 | 22 | 6 | 0 | 可运行，具备治理能力 |

### 4.2 最近成功记录

| 专项任务 | 最近成功时间 (UTC) | Run ID | 状态说明 |
|----------|--------------------|--------|----------|
| NPU Build and Test | 2026-04-02 23:38:48 | 23927010611 | NPU 构建和基础测试链路已成功跑通 |
| x86 Nightly 构建验证 | 2026-04-02 22:23:56 | 23924812258 | x86 nightly 继续稳定运行 |
| ARM Nightly 构建验证 | 2026-04-02 09:10:38 | 23893095476 | ARM nightly 已具备稳定成功案例 |
| Lint Ascend/pytorch | 2026-04-01 01:13:31 | 23827086198 | Lint 扫描链路可正常工作 |

## 5. 分阶段进展总结

| 阶段 | 专项任务 | 阶段成果 | 当前状态 |
|------|----------|----------|----------|
| 第一阶段 | x86 Nightly 构建验证 | 建立了每日自动验证 `Ascend/pytorch` 与 PyTorch nightly 编译兼容性的主链路 | 已完成 |
| 第一阶段 | ARM Nightly 构建验证 | 打通了 ARM 自托管 runner + 容器构建流程 | 持续优化中 |
| 第二阶段 | 昇腾 NPU 构建与测试 | 完成 build-and-test 一体化流程改造，已出现成功 run | 持续优化中 |
| 第二阶段 | PyTorch 主社区测试迁移 | 完成 `PrivateUse1/NPU` 适配机制、测试框架和迁移思路分析 | 分批落地中 |
| 第三阶段 | 静态扫描与规则治理 | 已建立 lint 规则迁移体系，具备结构化报告输出能力 | 已完成 |
| 第三阶段 | 问题分析与上游闭环 | 已建立失败分析、issue 沉淀和同步上游的流程基础 | 部分完成 |

## 6. 当前问题与瓶颈

| 专项任务 | 当前问题 | 表现 | 状态 | 说明 |
|----------|----------|------|------|------|
| ARM Nightly 构建验证 | self-hosted runner 调度不稳定 | 最近失败 run `23924845622` 未被 runner 接单 | 待解决 | 当前主要问题已从“构建流程设计”转向“runner 资源稳定性” |
| 昇腾 NPU 构建与测试 | NPU 环境初始化和运行时加载稳定性不足 | 代表性失败 run `23876199231` 失败于 `Verify NPU availability` | 待解决 | 当前问题集中在 CANN、挂载路径、`torch_npu` 导入和设备初始化 |
| PyTorch 主社区测试迁移 | 覆盖范围仍小 | 当前仍以基础验证和 smoke 测试为主 | 推进中 | 需在环境稳定后逐步扩大测试池 |
| issue 自动闭环 | 自动化程度仍不够高 | issue 修复判定、自动同步和报告输出仍可增强 | 推进中 | 适合作为后续平台化工作继续建设 |

## 7. 关键成果总结

| 成果项 | 内容 | 状态 |
|--------|------|------|
| 建立 nightly 兼容性验证能力 | 已具备持续验证 `Ascend/pytorch` 跟随 PyTorch nightly 演进的能力 | 已完成 |
| 建立 ARM 构建验证能力 | 已在 ARM / NPU 环境上成功构建 `torch_npu` wheel | 已完成 |
| 建立 NPU 基础测试能力 | 已完成 NPU build-and-test 链路打通，并已成功执行 | 持续优化中 |
| 建立静态扫描治理能力 | 已支持多类 lint 规则，对 `Ascend/pytorch` 做结构化扫描 | 已完成 |
| 建立问题发现和上游反馈能力 | 已能从 nightly / NPU 失败中提炼问题并沉淀 issue | 部分完成 |

## 8. 下一阶段计划

| 专项任务 | 下一步工作 | 目标 | 状态 |
|----------|------------|------|------|
| ARM / NPU 基础设施稳定化 | 提升 self-hosted runner 可用性，固化镜像与挂载配置 | 稳定任务调度和执行环境 | 计划中 |
| NPU 基础验证稳定化 | 固化 NPU availability 检查逻辑，维护最小 smoke 测试集 | 形成稳定的每日 NPU 基础验证能力 | 计划中 |
| 主社区测试扩展 | 从 `test_device.py` 扩展到 tensor、autograd、nn 等核心测试 | 建立 smoke / core / extended 三层测试池 | 计划中 |
| issue 自动闭环增强 | 自动生成报告、创建或更新 issue、同步上游 | 降低人工分析成本，强化平台属性 | 计划中 |

## 9. 汇报结论

| 结论项 | 内容 |
|--------|------|
| 项目阶段判断 | 项目已经完成从“方案设计”到“运行平台”的跨越 |
| 当前最成熟方向 | x86 nightly 构建验证 |
| 当前重点突破方向 | ARM / NPU 环境稳定性和主社区测试覆盖扩展 |
| 项目核心价值 | 持续发现 `Ascend/pytorch` 跟随 PyTorch nightly 演进中的兼容性问题，并推动问题闭环到上游 |
