# RC-026-R2.1 Legacy Spec Reconciliation

**Generated:** 2026-08-05
**Corrected:** 2026-10-10 (convergence re-review)
**Legacy Spec:** `tests/e2e/m6ui-slice4-preview.spec.js` (14 tests, M6-UI Slice 4)
**New Suite:** 7 spec files (G1–G15)

---

> **Correction notice (2026-10-10):** the "Fully Replaced" column below previously
> claimed ✅ for all 14 rows and the decision section stated "All 14 legacy tests
> are fully replaced". Independent re-review on convergence onto current `main`
> showed that **9 of the 14 browser-level contracts were not replaced at all** —
> the legacy spec was renamed unchanged into `tests/.archive-e2e/`, which lies
> outside Playwright's `testDir` (`playwright.config.js`) and therefore never
> executes. The table now records the true status. The affected *contracts* are
> still covered by Python integration tests, so this is a browser-coverage gap,
> not an untested product area.

---

## Mapping Table

`Browser replaced` = an equivalent browser-level test exists in the new suite.
`Contract covered` = the contract is exercised somewhere in the repository.

| # | Legacy Test | Contract | New Spec | Browser replaced | Contract covered |
|---|------------|----------|----------|:---:|:---:|
| 0 | Confirm candidate | Reference event confirmation | golden-path (G4) | ✅ | ✅ |
| 1 | Navigate to preview page | Calculation preview form | — | ❌ | ✅ `tests/integration/test_m6ui_slice4_calculation_preview.py` |
| 2 | Submit preview form | Calculation result display | — | ❌ | ✅ same |
| 3 | Verify trace steps | Deterministic calculation trace | — | ❌ | ✅ same |
| 4 | No external requests | Network isolation (privacy) | security-privacy (G12) | ✅ | ✅ |
| 5 | POST without CSRF = 403 | CSRF protection | security-privacy (G12) | ✅ | ✅ |
| 6 | Stale ID returns 409 | Conflict / expected-state binding | — (`test.fixme`; previously a no-op test) | ❌ | ✅ `tests/integration/test_m6ui_slice3_correct_revoke.py` |
| 7 | Non-existent = 404 | Error handling | error-states (G11) | ✅ | ✅ |
| 8 | Preview after revoke | Revoked state | — | ❌ | ✅ `tests/integration/test_m6ui_slice4_calculation_preview.py` |
| 9 | 1920×1080 viewport | Responsive: desktop | — | ❌ | ⚠️ no viewport assertion anywhere |
| 10 | 390×844 viewport | Responsive: mobile | — | ❌ | ⚠️ no viewport assertion anywhere |
| 11 | 1024×768 viewport | Responsive: tablet | — | ❌ | ⚠️ no viewport assertion anywhere |
| 12 | Axe on preview form | Accessibility | accessibility (G13) | ⚠️ axe was never executed (path defect, repaired in this branch) | ✅ on other pages once axe loads |
| 13 | Axe on preview result | Accessibility | accessibility (G13) | ⚠️ same | ⚠️ preview pages not scanned |

## Decision

The legacy spec is archived and **not** executed. Five browser-level contract
groups lose browser coverage: calculation preview form/result/trace,
revoked-state preview, three viewport checks, and axe scans of the preview
pages. The calculation-preview and revoked-state contracts remain covered by
Python integration tests; the three viewport checks are not covered anywhere.

Restoring the legacy spec into the executed set is tracked as follow-up work. It
is not a drop-in move: the spec spawns its own server on a fixed port (18000) and
writes to a hardcoded evidence directory, which conflicts with the
harness-driven suite introduced by this branch.

## Action

- Legacy spec archived at `tests/.archive-e2e/m6ui-slice4-preview.spec.js`
  (outside the Playwright `testDir`, therefore not executed)
- Coverage gap above recorded honestly rather than reported as fully replaced
- Historical evidence preserved for audit trail
