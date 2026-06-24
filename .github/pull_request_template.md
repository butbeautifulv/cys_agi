## Summary

<!-- What changed and why -->

## Checklist

- [ ] `./scripts/ruff_fix.sh` passes
- [ ] `uv run lint-imports` passes
- [ ] Domain coverage gate green (`--cov-fail-under=100`)
- [ ] **Security Shift Left** workflow green (`security-shift-left` — Gitleaks, SAST, OSA, IaC, Hadolint, Ruff)
- [ ] No new imports from `bootstrap` / `interfaces` into `cys_core/domain` or `cys_core/application`
- [ ] Adversarial tests run if security/ingress/tool/RAG/HITL paths changed

## Test plan

<!-- Commands run or manual steps -->
