创建每日定时 CI 分析任务，使用 CronCreate 在每天北京时间早上 8:00 自动执行分析流程。

---

## 执行步骤

### 第一步：拉取最新代码

```bash
git pull
```

### 第二步：使用 CronCreate 创建定时任务

调用 CronCreate 工具，配置如下：

- **cron**: `0 8 * * *`（每天北京时间早上 8:00）
- **recurring**: `true`（重复执行）
- **prompt**: 包含完整的分析流程指令

### 定时任务 Prompt 内容

定时任务触发时，将执行以下流程：

```
请按以下顺序严格执行，每个步骤完成后再执行下一个：

## 步骤 1：拉取最新代码

```bash
git pull
```

## 步骤 2：执行 analyze-failure

调用 Skill 工具执行 `analyze-failure`，分析最新失败的 CI 运行。

## 步骤 3：根据分析结果判断是否需要创建 issue

- 如果分析结果显示**编译失败**，继续执行 `report-issue`
- 如果分析结果显示**Workflow 脚本失败**，直接修复 `.github/workflows/*.yml`，无需创建 issue
- 如果分析结果显示**依赖/网络问题**，记录问题但不创建 issue
- 如果没有失败的 CI 运行，输出「无失败构建，跳过后续步骤」并结束

## 步骤 4：执行 report-issue（仅编译失败时）

调用 Skill 工具执行 `report-issue`，根据分析结果创建 issue 文档。

## 步骤 5：执行 sync-issues（仅成功创建 issue 时）

如果步骤 4 成功创建了新的 issue 文件，调用 Skill 工具执行 `sync-issues`，同步到 GitCode 平台。

---

## 重要约束

1. **严格按顺序执行**：analyze-failure → report-issue → sync-issues，不交叉混用
2. **条件执行**：根据上一步结果决定是否继续
3. **每次执行独立**：不依赖之前执行的状态
```

---

## CronCreate 调用示例

```json
{
  "cron": "0 8 * * *",
  "recurring": true,
  "prompt": "<上述 prompt 内容>"
}
```

---

## 输出结果

成功创建后，输出：

```
✓ 已创建定时 CI 分析任务

- 执行时间：每天北京时间 08:00
- 任务内容：拉取代码 → analyze-failure → report-issue → sync-issues
- 有效期：7 天（自动过期）

使用 /tasks 命令查看任务状态
```

---

## 注意事项

- 定时任务仅在本 Claude 会话期间有效，7 天后自动过期
- 若需要持久化任务，考虑使用 `/schedule` skill 配置远程触发器
- 任务仅在 REPL 空闲时执行，不会中断当前对话