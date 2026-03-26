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

---

## 13. Provider Profile 选择契约（BL-071）

为避免每次执行都手工从桌面文件提取 provider base/key，delegate 层现在支持
显式 provider profile 选择：

- 选择变量：`ARGUS_PROVIDER_PROFILE`
- profile 文件：`ARGUS_PROVIDER_PROFILES_FILE`
  - 未设置时默认读取：`contracts/provider_profiles.json`
  - 可参考模板：`contracts/provider_profiles.example.json`

### profile JSON 约定

支持两种结构：

- 顶层直接是 profile map
- 顶层 `{ "profiles": { ... } }`

每个 profile 可配置：

- `api_base` / `openai_api_base` / `base_url`
- `model_name` / `openai_model_name` / `model`
- `wire_api`
- `fallback_chat_urls`
- `fallback_response_urls`
- `fallback_api_bases`
- API key 任选其一：
  - `api_key`（不推荐明文）
  - `api_key_env`（推荐）
  - `api_key_secret`（容器 secret）

### 运行规则

1. 未设置 `ARGUS_PROVIDER_PROFILE` 时，保持旧版环境变量解析行为不变。  
2. 设置了 profile 时，profile 中给出的值覆盖默认环境解析结果。  
3. profile 引用的 `api_key_env` / `api_key_secret` 缺失时，fail-closed 并报错，避免静默回落到错误 provider。  

### BL-077 基线配置（仓库托管）

为减少临时 profile 文件漂移，仓库内提供了可复用基线文件：

- `contracts/provider_profiles.json`

其中 `fast_chat_governed_baseline` 对应 BL-076 验证通过路径：

- `api_base=https://fast.vpsairobot.com/v1`
- `wire_api=chat_completions`
- `model_name=gpt-5-codex`
- `api_key_env=OPENAI_API_KEY_FAST`

最小运行设置：

1. 导出 `OPENAI_API_KEY_FAST=<有效 key>`  
2. 导出 `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`  
3. 运行受管 execute（无需再生成临时 profiles 文件）  

### BL-080 重试预算运行建议（已冻结）

`execute_approved_previews.py` 的自动化瞬态重试预算由下列环境变量控制：

- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS`

冻结建议（基于 `runtime_archives/bl080/` 的受控对比样本）：

1. 默认保持 `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`。  
2. 不把默认值提升为 `2`，除非有新证据证明可显著提升 `processed` 通过率。  
3. `=2` 仅作为受控恢复窗口中的临时覆盖值使用，并在 run 结束后恢复默认。  

### BL-082 预算 `2` 临时升级触发与回滚 Runbook（产品化）

在保持默认 `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1` 的前提下，仅允许在满足触发条件时临时升级到 `=2`。

#### 触发条件（全部满足）

1. 当前执行对象是 `phase=now` 的阻塞项或明确优先级恢复窗口。  
2. 最近一次同目标受管 replay 在默认预算 `=1` 下因瞬态错误失败（`timeout/http_524/http_502`）。  
3. 已声明本次为“短窗口临时覆盖”，并约定 run 后立即回滚到默认预算。  

#### 执行步骤（受管 drill 口径）

1. 固定 provider 控制：  
   - `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`  
   - `ARGUS_PROVIDER_PROFILES_FILE` 置空/不设置  
   - `ARGUS_LLM_MAX_RETRIES=1`  
   - `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
2. 临时导出：`ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=2`。  
3. 执行一次受管 replay，并归档 execute/runtime/state 证据。  
4. 执行后立刻恢复默认：取消该临时环境变量，后续 run 回到预算 `=1`。  

#### 回滚条件（任一满足即回滚）

1. 本次 run 结束（不论 `processed` 成功或失败）。  
2. run 出现非瞬态失败或异常副作用信号。  
3. run 未带来可接受收益（例如通过率无改善但 wall-time 明显增加）。  

#### 证据要求

最少归档以下文件：

- `tmp/*execute*.json` 与 `tmp/*stderr*.log`
- `runtime/automation-*` 与 `runtime/critic-*`
- `state/<preview>.result*.json` 与 `state/<preview>*.json`
- 汇总记录触发原因、回滚时点与结论

### BL-084 JSON 修复路径运行建议（置信窗口）

针对 `ARGUS_LLM_JSON_REPAIR_ATTEMPTS` 的运行建议：

1. 默认保持 `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`（有界修复）。  
2. 不提高默认值，除非新增证据显示修复路径高频触发且对通过率有稳定正收益。  
3. 置信窗口观察口径至少包含：
   - `json_output_repair_attempts_used` 触发率
   - `json_invalid_terminal` 终止率
   - `processed`/`critic_verdict` 与 wall-time
4. 若窗口内失败主因仍是 `timeout`，优先处理上游时延/可用性，不将其误归因为 JSON 修复策略。  

### BL-085 JSON 修复已触发路径受控回放口径

当需要验证“修复路径本身”的行为（而非线上自然触发频率）时，使用受控
malformed-output 回放并归档证据，口径如下：

1. 首轮 automation 输出必须是非 JSON，随后 repair 轮返回合法 JSON。  
2. 必须记录请求轨迹，能够证明调用顺序是：
   - `automation_initial_invalid`
   - `automation_repair`
   - `critic_*`
3. 证据至少包含：
   - execute 结果 JSON/stderr
   - automation/critic 的 runtime + output + task 快照
   - request trace（标识初始失败与修复轮）
   - 汇总 TSV（`json_output_repair_attempts_used`、verdict、wall-time）
4. 该受控回放仅用于验证已触发路径，不改变默认参数：
   - `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`
   - `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`

### BL-086 timeout 主瓶颈优先级口径（跨窗口）

当跨窗口证据中 `timeout` 仍是主要失败类别时，运行优先级应固定如下：

1. 默认参数保持不变：  
   - `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`  
   - `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`
2. 在进入 JSON 路径参数调优前，先完成 timeout 路径治理：
   - provider 可用性与时延波动排查
   - fallback 端点/路由策略验证
   - timeout 恢复与回放证据归档
3. 若跨窗口统计满足：
   - `timeout_share_among_failures >= 0.6`
   - 且 `json_invalid_terminal_rate` 接近 `0`
   则默认判定 timeout 为当前首要阻塞项，不将主失败归因于 JSON 修复预算。
