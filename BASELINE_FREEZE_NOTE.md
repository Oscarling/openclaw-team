# BASELINE_FREEZE_NOTE

## A. 当前不可回退的不变量

- Manager 单入口（不新增绕过入口）
- Worker 一次性执行函数（start -> read task -> execute -> write result -> exit）
- contract-first（task/output contract 先行）
- 状态真相来自 `output.json.status`
- 外部输入默认只能到 preview
- approval 必须显式
- execute 必须独立
- replay protection 必须保留
- `needs_revision` 不等于链路故障

## B. 当前不要无必要重构的文件 / 模块

- `/Users/lingguozhong/openclaw-team/dispatcher/worker_runtime.py`
- `/Users/lingguozhong/openclaw-team/skills/delegate_task.py`
- `/Users/lingguozhong/openclaw-team/skills/execute_approved_previews.py`

关于 `skills/execute_approved_previews.py` 的准确口径：
- 当前控制链稳定，不要无必要重构。
- 未来若推进主线闭环确有必要，只允许做最小改动，不应视为永久不可碰。

## C. 当前测试基线

- 每阶段复跑基线不变量（approval gate、execute once、replay protection、Critic artifact 完整性）。
- 后续推进采用：
- 普通阶段：1 smoke + 3 regression
- 关键里程碑：5 formal validation rounds

## D. 当前 gating 规则

- 无 approval 不执行
- execute 必须独立
- 未来 Git 阶段中，`git push` 必须是 Trello writeback / Done 之前的硬门

## E. Trello Read-only -> Preview 去重冻结（当前 Phase）

当前冻结规则（方案 A）：
- 同一 `origin_id` 只允许一次 preview；后续同卡内容变更，不自动重新生成 preview。
- 默认仍按现有 `origin`-based dedupe 冻结；未显式声明 regeneration 时，命中 `origin:<origin_id>` 即去重。
- 当前新增的受控例外：外部输入若显式携带 `regeneration_token`，可按 `origin_regeneration:<origin_id>:<token>` 在同一 `origin_id` 下重新生成一个新的 preview；该 token 必须进入 preview / sidecar 证据链。

适用范围：
- 仅适用于当前 phase 的 `manager-side Trello read-only -> preview` 链路。

当前不支持：
- 同一张 Trello 卡片在内容更新后自动重进 preview。
- 未显式提供 `regeneration_token` 的同源重进 preview。

冻结原因：
- 保持最小改动。
- 与现有 `origin`-based dedupe 机制一致（即命中 `origin:<origin_id>` 即去重）。
- 在需要同源重生成时，仍然要求显式、可审计、非自动的重新入链。

未来可选升级（本阶段不做）：
- 按内容 `hash/version` 允许同卡变更后再入链。

明确不在本次冻结范围：
- execute / Git / Trello writeback。
- retry / 429 优化。
