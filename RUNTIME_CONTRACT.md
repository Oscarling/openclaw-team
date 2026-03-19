# Argus Runtime Contract

> 目的：把 Argus 当前阶段（Phase 3）的运行目录、任务类型、JSON 契约、任务命名规则一次性钉死，避免后续继续漂移。  
> 状态：已进入可用于模拟 Trello 派单的基线版本。

---

## 1. 当前阶段结论

当前已经完成：
- Manager / Architect / DevOps / Automation / Critic 的角色边界定义
- `openclaw.json` 基础骨架
- 终极业务主线 roadmap 固化

当前这一步要固定的，不是再讨论愿景，而是：

**把运行骨架定型，让 Manager 能稳定把模拟 Trello 需求转成标准任务载荷。**

---

## 2. 目录契约

Argus 现在区分两层路径：

### A. 逻辑路径（写入文档 / JSON / review 时使用）
统一使用相对路径：

- `artifacts/architecture/...`
- `artifacts/scripts/...`
- `artifacts/configs/...`
- `artifacts/reviews/...`
- `workspaces/manager/...`
- `workspaces/architect/...`
- `workspaces/devops/...`
- `workspaces/automation/...`
- `workspaces/critic/...`
- `tasks/...`

### B. 运行时挂载路径（Worker 实际读写时使用）
当前 Worker SOUL / 配置使用的运行时绝对路径为：

- `/app/artifacts/...`
- `/app/workspaces/<worker>/...`
- `/app/tasks/...`

### 统一规则
1. **Worker 运行时可以读写绝对路径。**
2. **所有对外说明、`output.json`、review 报告、Manager 汇总，一律回写相对路径。**
3. **禁止在最终返回结果里混用 `/app/...` 绝对路径与 `artifacts/...` 相对路径。**

也就是：

- 运行时可以写：`/app/artifacts/scripts/file_sync.py`
- 最终返回必须写：`artifacts/scripts/file_sync.py`

---

## 3. task_id 命名规则

为避免任务 ID 漂移，当前统一采用：

```text
<PREFIX>-<YYYYMMDD>-<NNN>
```

### Prefix 对应表
- `ARCH` → Architect
- `DEVOPS` → DevOps
- `AUTO` → Automation
- `CRITIC` → Critic

### 示例
- `ARCH-20260317-001`
- `AUTO-20260317-001`
- `CRITIC-20260317-001`

### 规则
1. 日期使用 UTC。
2. 同一天内同类任务序号从 `001` 递增。
3. `task_id` 一旦下发，不允许在执行链路中被二次改名。
4. Critic 对某个 Automation 产物进行审查时，应新建自己的 `CRITIC-*` 任务，而不是复用上游 `AUTO-*` 任务号。

---

## 4. Task Typing System

每个任务都必须定义 `task_type`。

这个字段用于明确：
- Worker 当前要执行的任务类别
- 期望产出的 artifact 形态
- 不能靠 Worker 自己猜测的执行语义

### 当前 V1 基线 task_type
- `design_architecture`
- `setup_infrastructure`
- `generate_script`
- `review_artifact`

### 当前默认映射
- `architect` → `design_architecture`
- `devops` → `setup_infrastructure`
- `automation` → `generate_script`
- `critic` → `review_artifact`

### 规则
1. Worker 不得在缺少 `task_type` 时自行猜测任务意图。
2. 如果未来扩展新的 `task_type`，必须先更新 schema 与本文档，再投入使用。
3. `task_type` 的作用是收紧执行语义，不是替代 `objective`。

---

## 5. Artifact Contract

Artifact 不再只是一条字符串路径。

标准结构为：

```json
{
  "path": "artifacts/scripts/file_sync.py",
  "type": "script"
}
```

### 当前允许的 artifact type
- `architecture`
- `script`
- `config`
- `review`
- `doc`

### 规则
1. `path` 必须使用相对路径，禁止写 `/app/...` 前缀。
2. `type` 必须反映 artifact 类别。
3. 在 `task.json` 中，`expected_outputs` 表示**计划产物**。
4. 在 `output.json` 中，`artifacts` 表示**实际产物**。
5. Worker 在 `status=success` 或 `status=partial` 时，只能声明真实存在的产物。

---

## 6. `task.json` 契约

### 必填字段
- `task_id`
- `worker`
- `task_type`
- `objective`
- `inputs`
- `expected_outputs`
- `constraints`

### 推荐附加字段
- `priority`
- `source`
- `acceptance_criteria`
- `metadata`

### 最小示例

```json
{
  "task_id": "AUTO-20260317-001",
  "worker": "automation",
  "task_type": "generate_script",
  "objective": "Generate a Python file sync script from a simulated Trello request.",
  "inputs": {
    "source_card": "openclaw-team/examples/simulated_trello_card_file_sync.json",
    "params": {
      "script_name": "file_sync.py"
    }
  },
  "expected_outputs": [
    {
      "path": "artifacts/scripts/file_sync.py",
      "type": "script"
    }
  ],
  "constraints": [
    "must support --dry-run",
    "must run from CLI",
    "must not access Trello directly"
  ]
}
```

### 解释规则
- `worker` 必须和目标 Worker 一致。
- `task_type` 必须和当前任务语义一致。
- `inputs` 只放执行所需上下文，不放大段模糊叙述。
- `expected_outputs` 必须使用结构化 artifact 对象。
- `constraints` 必须是可验证约束；即使没有硬约束，也应传 `[]`，不要省略字段。

---

## 7. `output.json` 契约

### 必填字段
- `task_id`
- `worker`
- `status`
- `summary`
- `artifacts`
- `timestamp`

### 可选字段
- `errors`
- `notes`
- `metadata`
- `duration_ms`

### 最小示例

```json
{
  "task_id": "AUTO-20260317-001",
  "worker": "automation",
  "status": "success",
  "summary": "Generated a CLI file sync script with dry-run support.",
  "artifacts": [
    {
      "path": "artifacts/scripts/file_sync.py",
      "type": "script"
    }
  ],
  "timestamp": "2026-03-17T10:30:00Z",
  "duration_ms": 1820
}
```

### `status` 当前允许值
- `success`
- `failed`
- `partial`

### 输出规则
1. `artifacts` 必须全部使用结构化 artifact 对象。
2. `summary` 必须对应真实产物，不允许虚构完成。
3. `failed` 时应尽量给出 `errors`。
4. `partial` 只用于确实产出部分结果、但未完全满足目标的情况。
5. `status` 为 `success` 或 `partial` 时，`artifacts` 至少应包含一个真实产物。

---

## 8. Input Source Rules

Workers 必须把所有输入都视为 **Manager 转译后的任务输入**。

Workers MUST NOT：
- 自行补全不存在的外部上下文
- 直接访问 Trello / Git / Telegram / 外部入口
- 假设 `task.json` 中未出现的背景已经默认存在

如果完成任务所需输入缺失：

```text
→ Worker 应明确失败
→ 在 output.json 中写出 errors
→ 不得假装成功
```

---

## 9. Trello → Manager → Worker 转译规则

Argus 的宪法不允许 Worker 直接读取 Trello。

因此标准转译链路必须是：

```text
Trello Card
→ Manager 读取并解析
→ Manager 提取 task_type / objective / inputs / expected_outputs / constraints
→ Manager 生成 task.json
→ Worker 执行
→ Worker 输出 output.json + artifacts
```

### 关键约束
- Automation 不直接读 Trello
- Critic 不直接读 Trello
- DevOps 不直接读 Trello
- 只有 Manager 可以处理外部入口与业务上下文转译

---

## 10. 当前已准备好的示例文件

为进入 Phase 4，这次已同步准备：

- `openclaw-team/contracts/task.schema.json`
- `openclaw-team/contracts/output.schema.json`
- `openclaw-team/examples/simulated_trello_card_file_sync.json`
- `openclaw-team/examples/tasks/AUTO-20260317-001.task.json`
- `openclaw-team/examples/tasks/CRITIC-20260317-001.task.json`

这些文件的作用是：

**让 Manager 的第一条“模拟 Trello 需求 → Automation → Critic”链路有了统一输入样本。**

---

## 11. 当前下一步

基于这份契约，项目下一步建议固定为：

1. 用示例 Trello 卡片跑一次 Manager 任务转译
2. 验证 `AUTO-20260317-001.task.json` 是否足够驱动 Automation
3. 验证 `CRITIC-20260317-001.task.json` 是否足够驱动审查链路
4. 再进入真正的“模拟 Script 生成闭环测试”

---

## 12. 一句话结论

Argus 当前已经从“只讨论架构”推进到：

> **目录、契约、任务类型、任务样本都已可落盘；下一步应直接用模拟 Trello 卡片跑第一次标准任务转译。**
