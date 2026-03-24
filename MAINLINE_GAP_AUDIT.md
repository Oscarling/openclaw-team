# MAINLINE_GAP_AUDIT

> Status note (2026-03-24): this file is the `Phase 8F` gap snapshot. It is not
> the live current-state ledger. For the latest real state, use
> `PROJECT_CHAT_AND_WORK_LOG.md` and the relevant capability evidence reports such
> as `PROCESSED_FINALIZATION_REPORT.md`. The Git / Trello closure rows below
> predate the later processed-finalization helper and should not be read as the
> current capability map.

## A. 当前 stable baseline 摘要

当前已稳定链路：

`local_inbox -> ingest -> preview -> approval -> execute -> Automation -> Critic`

已验证通过的不变量：
- replay protection 已通过（5/5）
- Critic failed = 0
- Critic missing artifact = 0
- `needs_revision` 属于业务评审结果，不是链路故障

关键依据：
- `/Users/lingguozhong/openclaw-team/FULL_CHAIN_OPERATIONAL_VALIDATION_REPORT_V2.md`
- `/Users/lingguozhong/openclaw-team/CRITIC_PATH_DIAGNOSIS_REPORT.md`

## B. 主线目标摘要

主线目标：

`Trello read-only -> adapter -> preview -> approval -> execute -> Git add -> Git commit -> Git push -> Trello writeback -> Trello Done`

## C. 主线状态表

| 环节 | 状态 | 依据（真实文件路径） | blocker | 一句话说明 |
|---|---|---|---|---|
| Trello read-only | partial | `/Users/lingguozhong/openclaw-team/skills/trello_readonly_prep.py` | yes | GET-only 读取流程已实现，但真实连通仍受凭据缺失阻塞。 |
| adapter mapping | implemented | `/Users/lingguozhong/openclaw-team/adapters/trello_readonly_adapter.py` | no | Trello card 到标准 external input 的映射函数已落地。 |
| preview | implemented | `/Users/lingguozhong/openclaw-team/skills/ingest_tasks.py` | no | ingest 已能生成 `preview/*.json` 且默认 `pending_approval`。 |
| approval | implemented | `/Users/lingguozhong/openclaw-team/skills/execute_approved_previews.py` | no | 仅 `approvals/<preview_id>.json` 且 `approved=true` 才进入执行。 |
| execute | implemented | `/Users/lingguozhong/openclaw-team/skills/execute_approved_previews.py` | no | execute 独立入口稳定，含 replay protection。 |
| Automation / Critic | implemented | `/Users/lingguozhong/openclaw-team/adapters/local_inbox_adapter.py` + `/Users/lingguozhong/openclaw-team/skills/execute_approved_previews.py` | no | 已形成 Automation→Critic 编排，并有证据注入与 verdict 归一。 |
| final decision / processed / rejected | implemented | `/Users/lingguozhong/openclaw-team/skills/execute_approved_previews.py` + `/Users/lingguozhong/openclaw-team/skills/ingest_tasks.py` | no | final decision 已写回 preview，ingest 流转与 sidecar 完整。 |
| Git add | doc_only | `/Users/lingguozhong/openclaw-team/PHASE8B_EXTERNAL_FLOW_REPORT.md` | yes | 文档声明未接入自动化，仓库未发现 pipeline 代码入口。 |
| Git commit | doc_only | `/Users/lingguozhong/openclaw-team/PHASE8C_RECOVERY_TRELLO_READONLY_REPORT.md` | yes | 同上，当前仅文档层口径，未实现自动 commit。 |
| Git push | doc_only | `/Users/lingguozhong/openclaw-team/PHASE8E_PREVIEW_APPROVAL_REPORT.md` | yes | 同上，当前明确未启用 push 自动化。 |
| Trello writeback | doc_only | `/Users/lingguozhong/openclaw-team/PHASE8D_TRELLO_READONLY_REPORT.md` | yes | 当前阶段明确禁写 Trello，仅保留只读准备。 |
| Trello Done | missing | （未定位到实现文件） | yes | 未发现卡片状态推进到 Done 的真实实现入口。 |

## D. 当前真正的 top 3 主线缺口

1. Trello 真实只读凭据缺失
2. Git add / commit / push 自动化链路未实现
3. Trello writeback + Trello Done 未实现

## E. 当前最稳的下一步

- 先完成并验证 Trello 凭据可见性
- 只解锁 `Trello read-only -> adapter mapping -> preview`
- 先不碰 Git / writeback / Done

## F. 当前不建议做的事

- 新业务类型扩张
- 扩 agent 数量或职责面
- 非主线集成扩张
- 非 blocker 的 Phase 6 内核重构

## G. 8F -> 8M 最小实施路线图

统一规则（适用于以下阶段）：
- 普通阶段测试节奏：`1 smoke + 3 regression`
- 关键里程碑冻结：`5 formal validation rounds`
- `git push` 是 Trello writeback / Trello Done 之前的单独硬门：没有 push success，不允许 writeback，不允许 Done
- 当前最稳的下一步：先执行 Phase 8G，只解锁 `Trello read-only -> adapter -> preview`，先不碰 Git / writeback / Done

### Phase 8F：基线冻结 + gap audit
1. 目标：冻结当前 stable baseline 与主线缺口口径，防止后续目标漂移。  
2. 预计改动范围：`MAINLINE_GAP_AUDIT.md`、`BASELINE_FREEZE_NOTE.md`（文档层）。  
3. 测试建议：文档核对 + 现有 V2 结果复核（按 `1 smoke + 3 regression` 口径对齐，不新增执行任务）。  
4. 风险 / blocker：口径不统一导致后续阶段误判“稳定性 vs 业务评审”。  
5. 退出条件：基线不变量、主线状态表、top3 缺口、下一步硬门口径全部固化。  

### Phase 8G：Trello 凭据注入 + 只读 smoke
1. 目标：打通真实 Trello 只读最小连通（GET-only）。  
2. 预计改动范围：运行态环境（host / `.env` / manager 容器）；使用 `skills/trello_readonly_prep.py` 做 smoke。  
3. 测试建议：`1 smoke + 3 regression`，重点验证凭据可见性与只读读取稳定性。  
4. 风险 / blocker：凭据缺失或作用域不正确（board/list ID 不匹配）。  
5. 退出条件：只读 smoke pass，且不发生任何 Trello 写操作。  

### Phase 8H：Trello -> Preview
1. 目标：把真实 Trello card 映射为标准输入并稳定落到 `preview/*.json`（pending_approval）。  
2. 预计改动范围：`adapters/trello_readonly_adapter.py`、`skills/trello_readonly_prep.py`、`skills/ingest_tasks.py`（如需最小对接）。  
3. 测试建议：`1 smoke + 3 regression`，验证 preview 结构、dedupe、审批前不执行。  
4. 风险 / blocker：字段映射不稳定导致 ingest reject 或 preview 结构不一致。  
5. 退出条件：Trello 来源输入可稳定生成 preview，且全部停留 pending_approval。  

### Phase 8I：Trello-sourced Approval / Execute
1. 目标：在不绕过 gate 的前提下，完成 Trello 来源 preview 的审批与执行闭环。  
2. 预计改动范围：`skills/execute_approved_previews.py`（仅必要最小调整）、审批文件流与 sidecar。  
3. 测试建议：`1 smoke + 3 regression`，验证 approval gate、execute once、replay protection。  
4. 风险 / blocker：来源标识与审计记录不足，导致执行追踪不清晰。  
5. 退出条件：Trello 来源任务与 local_inbox 一样满足控制链不变量。  

### Phase 8J：Git dry-run / no-push
1. 目标：实现 Git 阶段前的安全演练（仅 dry-run，不做 push）。  
2. 预计改动范围：manager-side Git helper（新脚本或 skill）、审计日志与结果 sidecar。  
3. 测试建议：`1 smoke + 3 regression`，验证 add/commit 预检与失败回滚语义。  
4. 风险 / blocker：误触真实提交或污染工作区。  
5. 退出条件：dry-run 可稳定输出“将执行什么”，且不改变远端状态。  

### Phase 8K：真实 Git commit（本地）
1. 目标：在受控条件下执行本地真实 commit（不 push）。  
2. 预计改动范围：Git helper 与提交信息规范；最小化影响范围到目标文件集合。  
3. 测试建议：`1 smoke + 3 regression`，验证 commit 仅包含期望文件且可追溯。  
4. 风险 / blocker：提交范围失控、混入无关改动。  
5. 退出条件：本地 commit 稳定成功且提交内容可审计。  

### Phase 8K2：真实 Git push（单独硬门）
1. 目标：将 push 作为独立阶段和硬门，不与 writeback 混跑。  
2. 预计改动范围：Git push helper、权限与失败重试策略。  
3. 测试建议：`1 smoke + 3 regression`，关键里程碑前补 `5 formal validation rounds`。  
4. 风险 / blocker：远端权限/网络失败，或推送到错误分支。  
5. 退出条件：push success 被可靠记录；未成功则明确阻断后续 writeback/Done。  

### Phase 8L：Trello writeback / Done
1. 目标：在 push success 之后，执行 Trello 状态写回与 Done 流转。  
2. 预计改动范围：新增 Trello write API 层（与 read-only 分离）、状态映射与审计日志。  
3. 测试建议：`1 smoke + 3 regression`，验证写回幂等、失败可重试、不可越权。  
4. 风险 / blocker：误更新卡片、重复写回、状态映射错误。  
5. 退出条件：仅在 push success 后触发 writeback，Done 状态与本地结果一致。  

### Phase 8M：主线全链回归与冻结
1. 目标：对主线目标链路做最终回归并冻结基线。  
2. 预计改动范围：以验证和文档冻结为主，代码仅限 blocker 修复。  
3. 测试建议：关键里程碑执行 `5 formal validation rounds`。  
4. 风险 / blocker：阶段间口径不一致导致“通过标准”偏移。  
5. 退出条件：主线链路闭环通过、blocker 清零、冻结文档更新完成。  
