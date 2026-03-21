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
