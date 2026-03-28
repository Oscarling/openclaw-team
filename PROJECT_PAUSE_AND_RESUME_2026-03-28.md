# 项目阶段性暂停与重启说明（2026-03-28）

## 1. 当前冻结快照

- 当前工作分支：`bl094-endpoint-chain-recovery-local`
- 当前关键提交（按时间倒序）：
  - `ee9108f` feat: prevalidate summary schema in persisted report consistency checks
  - `caeed78` feat: harden snapshot guard summary path and source parity checks
  - `25d93ce` feat: add snapshot guard summary validation and input hardening
- `main` 与 `origin/main` 已对齐（本地检查一致）。

## 2. 目前可确认状态

- 本地治理与一致性硬化链路已连续通过：
  - `python3 scripts/backlog_lint.py`
  - `python3 scripts/backlog_sync.py`
  - `bash scripts/premerge_check.sh`（Warnings: 0, Failures: 0）
- Snapshot guard 相关 summary/report/history 一致性门禁已加强并落地。

## 3. 仍未闭环的外部阻塞

- `BL-20260326-099` 依赖外部可用 `key/base` 路由；当前旧路由存在高波动（含 5xx / TLS EOF / 鉴权异常）风险。
- 在外部路由稳定前，不建议将实网回放结果作为最终验收结论。

## 4. 后续重启建议（最短路径）

1. 切换到保存分支：
   - `git switch bl094-endpoint-chain-recovery-local`
2. 同步最新远端：
   - `git fetch origin`
   - `git pull --ff-only`
3. 先做本地门禁自检：
   - `python3 scripts/backlog_lint.py`
   - `python3 scripts/backlog_sync.py`
   - `bash scripts/premerge_check.sh`
4. 若要继续实网验收，再执行 provider/key-base 探测与回放。

## 5. 并行优化分支策略

- 建议在独立分支进行“抗波动优化”（断路器、健康评分、阈值验收），避免影响当前可回滚基线。
- 优化完成后通过 PR 合并，保持主线与优化线隔离。

## 6. 约定

- 本说明文件用于阶段性封存与快速恢复，不替代 `PROJECT_BACKLOG.md` 与 `PROJECT_CHAT_AND_WORK_LOG.md` 的正式记录职责。
