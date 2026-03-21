# OpenClaw 项目聊天与工作记录（截至当前会话）

> 说明：本文件基于当前对话与已执行操作整理，聚焦“做了什么、结果如何、当前状态是什么”。
> 不包含任何密钥明文。

## 1. 项目目标与边界

- 宿主机项目目录：`~/openclaw-team`
- 核心目标：在不破坏 Phase 6 内核的前提下，逐步完成
  - 多 Agent 基础搭建
  - Docker 化与热更新
  - Runtime / Contract 对齐与 hardening
  - Phase 7（PDF→Excel 业务试点）
  - Phase 8（外部输入流：inbox/adapter/preview/approval）
  - Full-chain operational validation（链路稳定性验证）
- 明确约束长期保持：
  - Manager 为唯一入口/调度器
  - Worker 一次性执行、文件通道通信
  - 不绕过 preview/approval gate
  - 多次要求下均未改 `delegate_task.py` / `worker_runtime.py`（除非明确历史任务要求）

## 2. 关键阶段纪要（按推进主线）

### Phase 0-2：基础结构与核心配置落地

- 创建并写入基础目录与文件：
  - `agents/manager/SOUL.md`
  - `agents/manager/AGENTS.md`
  - `skills/delegate_task.py`
  - `dispatcher/worker_runtime.py`
  - `openclaw.json`
  - `agents/architect/SOUL.md`
  - `agents/devops/SOUL.md`
- 做过“逻辑安全审查（dry run）+ 物理写入执行”流程，重点审查：
  - 仅 manager 具备 bindings 外部路由
  - worker（architect/devops 等）无状态、无路由、一次性执行、禁止互通

### Docker 基础设施与可运行性修复

- 补齐并写入：
  - `docker-compose.yml`
  - `containers/manager/Dockerfile`
  - `containers/worker/Dockerfile`
- 处理 `pip install docker` 代理问题：
  - manager Dockerfile 中加入清空代理变量
  - 使用清华镜像源安装

### 热更新能力修复

- `docker-compose.yml` 增加卷挂载（`dispatcher/skills/agents` 等）
- 执行 `docker compose down && docker compose up -d`
- 目标：避免镜像静态 COPY 导致代码更新不生效

### Runtime / Contract / Hardening 持续推进

- 多轮按清单执行：
  - contract 对齐
  - schema 验证
  - phase6 稳定化
  - hardening 回归
- 完成过测试资产同步与导入基准修复，确保测试引用当前仓库代码而非错误路径。

### Phase 7：业务试点（PDF→Excel）

- 基于真实目录 `~/Desktop/pdf样本` 进行 pilot
- 形成过脚本、review、业务报告
- 后续执行过环境修复（OCR 依赖检查与安装指引）
- 完成“收口任务”：保留产物、补 usage 文档、更新报告、避免真实业务数据入库

### Phase 7.2：稳定性回归

- 执行多轮回归与受控失败验证
- 目标聚焦“状态可信、失败诚实、不串任务、不假成功”

### Phase 8A/8B/8C：外部流模拟到硬化

- 建立并强化：
  - `inbox/ processing/ processed/ rejected/ adapters/ preview/ approvals`
- 实现并强化 local_inbox adapter：
  - 输入校验
  - 合法性校验
  - 去重/幂等
  - 状态流转
  - 结果侧写
- 完成多轮 feed→preview 验证：单条/批量/非法输入

### Phase 8D/8E：Trello 只读准备与 preview+approval 控制层

- 明确执行策略：
  - 先检查凭据是否存在（仅回传 SET/MISSING）
  - 无凭据不伪造成功
- 建立“外部输入默认只到 preview，不可直接执行”控制语义
- 通过显式 approval 才允许进入 execute

### Full-chain Operational Validation

- 完成过 1 轮 smoke，再推进到 5 轮正式验证
- 发现过 Critic 路径不稳定（历史）：
  - 有 failed 且无 artifact
  - 有 partial
  - 多轮 needs_revision
- 随后执行“Critic 路径诊断与最小收敛修复（不改 Phase6 内核）”

## 3. Critic 路径诊断与收敛（本轮前后关键结果）

### 已定位的历史根因

- Round1 failed 根因：Critic 输出契约未稳定满足（success/partial 语义下未带 artifact）
- Round5 partial 根因：Critic 证据输入组织不足（仅路径，缺少稳定可读快照）

### 最小收敛改动（仅 Critic 相关 shaping）

- 修改：`skills/execute_approved_previews.py`
  - verdict 提取归一增强
  - 注入 artifact 快照
  - 注入 review contract/template
  - 强化 Critic 约束
- 修改：`adapters/local_inbox_adapter.py`
  - 强化 Critic 任务 objective/constraints（明确 verdict 与 review artifact）
- 产出诊断报告：
  - `CRITIC_PATH_DIAGNOSIS_REPORT.md`

### 收敛后 3 轮 smoke

- 结果：Critic 无 failed、无缺 artifact、replay protection 正常
- 结论：Critic 路径从“偶发失稳”收敛到“可解释且可复现”

## 4. Full-chain Validation V2（本次最新执行）

> 你要求将“链路稳定性”与“业务评审结果”严格分离验收。

- 已执行 5 轮完整链路（inbox→ingest→preview→approval→execute→Automation→Critic→replay check）
- 新报告：`FULL_CHAIN_OPERATIONAL_VALIDATION_REPORT_V2.md`

### V2 结论（分离口径）

- Chain Stability：`stable`
  - Critic failed = 0
  - Critic 无 review artifact = 0
  - replay protection = 5/5
  - 无误执行、无重复执行、无残留异常态
- Business Review Outcome：
  - verdict pass = 1
  - verdict needs_revision = 4
  - verdict fail = 0
  - partial = 0
  - processed = 1
  - rejected = 4
  - `needs_revision` 原因可解释且总体一致

## 5. 最近可确认的提交记录（本会话可见）

- `d5e954b`  
  `stabilize critic path shaping and add diagnosis report`
- `4226d14`  
  `full-chain operational validation v2 report finalized`

## 6. 当前项目状态（简述）

- 控制链（preview/approval/execute/replay）已验证稳定。
- Critic 路径已完成一轮针对性诊断与最小收敛。
- 业务评审结果（pass/needs_revision）与链路故障已成功分离统计。
- 当前可基于既有口径继续做后续阶段（例如更多轮次或新业务模板），但不应把 `needs_revision` 直接等同于“系统不稳定”。

---

生成时间（UTC）：`2026-03-20`
