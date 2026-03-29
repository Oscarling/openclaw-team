# Opportunity Scan Stress Regression Report (2026-03-29)

Real-model pressure regression with 5 additional samples (`--test-mode off`).

| Sample | Title | Preview ID | Critic Verdict | GO/WATCH/NO-GO | Top Priority | Auto/Critic Runtime | Endpoint |
|---|---|---|---|---|---|---|---|
| 1 | 压力回归201：本地门店增收服务组合 | preview-manual-opportunity-scan-stress-201-7eeca88e8c53 | pass | 1/1/1 | 门店抖音团购文案改写服务 (GO) | 42.0s / 27.2s | https://api.deepseek.com/v1/chat/completions |
| 2 | 压力回归202：求职与人效微产品 | preview-manual-opportunity-scan-stress-202-8ec4fd24e6ca | pass | 1/1/1 | 面试问答个性化训练器 (GO) – Highest priority due to best fit for quick launch and feedback. | 47.8s / 28.3s | https://api.deepseek.com/v1/chat/completions |
| 3 | 压力回归203：内容变现轻服务 | preview-manual-opportunity-scan-stress-203-68140c7c9e27 | pass | 1/1/1 | 公众号选题库定制服务 (GO) - Highest priority: optimal balance of price, repurchase potential, and alignment with constraints. | 47.9s / 32.6s | https://api.deepseek.com/v1/chat/completions |
| 4 | 压力回归204：跨境卖家支持服务 | preview-manual-opportunity-scan-stress-204-4c55433b4dae | pass | 1/1/1 | GO - 亚马逊Listing首图文案优化 (最高优先级) | 50.9s / 31.9s | https://api.deepseek.com/v1/chat/completions |
| 5 | 压力回归205：教育培训辅助服务 | preview-manual-opportunity-scan-stress-205-63ec2e93527a | pass | 1/1/1 | GO - 教培机构朋友圈招生文案包: Top priority due to alignment with all constraints and quick validation path. | 40.5s / 21.1s | https://api.deepseek.com/v1/chat/completions |

## Artifacts

### Sample 1
- Analysis: `artifacts/analysis/opportunity_scan_manual-opportunity-scan-stress-201_7eeca88e.md`
- Review: `artifacts/reviews/opportunity_scan_manual-opportunity-scan-stress-201_7eeca88e_review.md`

### Sample 2
- Analysis: `artifacts/analysis/opportunity_scan_manual-opportunity-scan-stress-202_8ec4fd24.md`
- Review: `artifacts/reviews/opportunity_scan_manual-opportunity-scan-stress-202_8ec4fd24_review.md`

### Sample 3
- Analysis: `artifacts/analysis/opportunity_scan_manual-opportunity-scan-stress-203_68140c7c.md`
- Review: `artifacts/reviews/opportunity_scan_manual-opportunity-scan-stress-203_68140c7c_review.md`

### Sample 4
- Analysis: `artifacts/analysis/opportunity_scan_manual-opportunity-scan-stress-204_4c55433b.md`
- Review: `artifacts/reviews/opportunity_scan_manual-opportunity-scan-stress-204_4c55433b_review.md`

### Sample 5
- Analysis: `artifacts/analysis/opportunity_scan_manual-opportunity-scan-stress-205_63ec2e93.md`
- Review: `artifacts/reviews/opportunity_scan_manual-opportunity-scan-stress-205_63ec2e93_review.md`

## Summary

- Processed: 5/5
- Critic verdict `pass`: 5/5
- Rejected: 0/5
- Endpoint consistency: all runs used `https://api.deepseek.com/v1/chat/completions`
