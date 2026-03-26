创建每日定时 CI 分析任务，使用 CronCreate 在每天北京时间早上 8:00 自动执行分析流程。

---

## 创建定时任务

调用 CronCreate 工具，配置如下：

```json
{
  "cron": "0 8 * * *",
  "recurring": true,
  "prompt": "<见下方定时任务 Prompt>"
}
```

---

## 定时任务 Prompt

以下内容作为 CronCreate 的 `prompt` 参数，任务触发时在新上下文中执行：

```
请按以下顺序严格执行，每个步骤完成后再执行下一个：

## 步骤 1：拉取最新代码

```bash
git pull
```

## 步骤 2：执行 analyze-failure

调用 Skill 工具执行 `analyze-failure`，分析最新失败的 CI 运行。

## 步骤 3：执行 report-issue

调用 Skill 工具执行 `report-issue`。（该 skill 内部会判断失败类型，决定是否创建 issue 文件）

**注意**：如果 `report-issue` 判断为 CI 脚本失败需要修复 workflow，应直接修复 `.github/workflows/*.yml`。

## 步骤 4：执行 sync-issues

如果步骤 3 成功创建了新的 issue 文件，调用 Skill 工具执行 `sync-issues`，同步到 GitCode 平台。

---

## 重要约束

1. **严格按顺序执行**：analyze-failure → report-issue → sync-issues，不交叉混用
2. **条件执行**：根据上一步结果决定是否继续
3. **每次执行独立**：不依赖之前执行的状态
```

---

## 输出结果

成功创建后，输出：

```
✓ 已创建定时 CI 分析任务

- 执行时间：每天北京时间 08:00
- 任务内容：拉取代码 → analyze-failure → report-issue → sync-issues
- 有效期：7 天（自动过期）
- 每次在独立上下文中执行

使用 /tasks 命令查看任务状态
```

---

## 注意事项

- 定时任务每次触发时在**独立上下文**中执行，相当于自动 clear
- 任务仅在本 Claude 会话期间有效，7 天后自动过期
- 若需要持久化任务，考虑使用 `/schedule` skill 配置远程触发器
- 任务仅在 REPL 空闲时执行，不会中断当前对话