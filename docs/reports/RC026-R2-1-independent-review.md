# RC-026-R2.1 Independent Review — CORRECTED

**Originally generated:** 2026-08-05
**Original reviewer:** Hermes Agent (independent verification)
**Original branch:** `test/rc026-playwright-e2e-closure`
**Original base:** `origin/main @ a26968b`
**Original verdict:** `APPROVED`

> ## Correction notice (2026-10-10)
>
> This file previously recorded an unconditional `APPROVED` verdict and a
> `Playwright 105/105` GREEN gate for PR #13. On convergence of that branch
> onto current `main` (`39cc098`, merge `68c5568`) the work was re-reviewed
> independently. Several of the claims below were **falsified by the branch's own
> committed evidence**, and the defects were repaired before merge.
>
> The original content is preserved by reference; the table below records what
> was actually verified and what was wrong. The verdict is withdrawn.
>
> **Rule applied:** a PASS that cannot be reproduced from the committed evidence
> is not a PASS. Where a gate was never measured, it is recorded as unmeasured —
> not as green.

---

## Corrected review items

| # | Original claim | Corrected finding | Evidence |
|---|----------------|-------------------|----------|
| 1 | All 5 original failures resolved | Partially confirmed for cross-case API field name and form-based CSRF. Not confirmed for the idempotency assertion, which was tautological (see #11). | `tests/e2e/idempotency.spec.js` (pre-fix `expect(successCount).toBeGreaterThanOrEqual(0)`) |
| 2 | All 3 original skips replaced with real tests | Not confirmed. The CSRF nonce cookie test could never observe a cookie: it loaded `/ui/cases`, which by design sets no cookie, and returned early without asserting. | `src/private_legal_navigator/api/ui_routes.py:110-134` (no cookie) vs `:143-175` (cookie set) |
| 3 | Legacy spec mapped and archived — 14/14 fully replaced | **FALSE.** 9 of the 14 legacy browser contracts were not replaced: calculation preview form, preview result, deterministic trace, preview-after-revoke, and three viewport checks, plus two axe scans. The legacy spec was renamed unchanged into `tests/.archive-e2e/` and is outside Playwright's `testDir`, so it never executes. The contracts remain covered at Python integration level. | grep for `Berechnung`, `overflow`, `scrollWidth`, `revoke` in `tests/e2e/*.spec.js` → 0 matches; `tests/integration/test_m6ui_slice4_calculation_preview.py` |
| 4 | CSRF via real browser interaction | Confirmed (token read from the real form and submitted via `fetch`). | `tests/e2e/idempotency.spec.js`, `tests/e2e/security-privacy.spec.js` |
| 5 | Cookie contract documented (`pln_csrf_nonce`, HttpOnly, path=/ui) | Confirmed against the implementation, but the test asserting it did not exercise it (see #2). Test corrected to load the route that actually issues the cookie and to assert all four attributes. | `src/private_legal_navigator/api/ui_routes.py:166-174` |
| 6 | Idempotency case verified — API does not enforce title uniqueness | Confirmed as a statement about the API. The test was nevertheless rewritten to assert the contract in its own name ("at most 1 record"), which it previously did not. | `tests/e2e/idempotency.spec.js` |
| 7 | Seeded fault: CSRF token check | Confirmed for `POST` without CSRF → 403. | `tests/e2e/security-privacy.spec.js` |
| 8 | Installed-wheel import verified | Confirmed by the harness, which fails hard if the import does not come from `site-packages`. | `scripts/run-installed-wheel-playwright-e2e.py:64-77` |
| 9 | Anti-flakiness: 3 consecutive runs, 105/105, 0 flaky | **Not reproducible from the repository.** Only one report is committed, produced in a different checkout (`/media/xxammaxx/projekte/Rechtssoftware-rc026-playwright`) whose SHA was not recorded. Treat "3 consecutive runs" as unverified. | `evidence/rc026-r2/playwright/playwright-report.json:4-9` |
| 10 | Playwright 105/105, Pytest 1087 + 4 Frozen-RED | The Playwright count is plausible but the suite was not fully green as a *gate*: the accessibility gate was never executed (see #12a). The pytest figures predate the BescheidPilot import and are stale for current main. | see #12a; `tests/bescheidpilot_test_*.py` (284 tests) |
| 11 | No tautological assertions (0 `or True`, 0 `catch.*ignore`, 0 `waitForTimeout`) | **FALSE.** The greps did not cover the actual tautology: `expect(successCount).toBeGreaterThanOrEqual(0)` in `tests/e2e/idempotency.spec.js`, which is true for any count and can never fail. A count-based assertion is now in place. | `tests/e2e/idempotency.spec.js` (pre-fix) |
| 12 | No relevant skips — all `test.skip` removed or replaced with "graceful returns" | **FALSE and misleading.** The "graceful returns" were silent no-op passes: tests that returned early, wrapped assertions in `if (count > 0)`, or performed no request at all, while still being reported as passing. Repaired. | `tests/e2e/error-states.spec.js` (409), `tests/e2e/legal-timeline.spec.js`, `tests/e2e/golden-path.spec.js` |
| 12a | (implied) Accessibility gate GREEN | **FALSE.** `tests/e2e/axe-helper.js` resolved axe to `tests/src/private_legal_navigator/presentation/static/axe.min.js`, which does not exist. On miss it logged a warning and returned `{violations: []}`, so every axe assertion passed vacuously. The branch's own committed report contains the warning 7 times, covering the accessibility spec's axe tests. The gate was therefore **never measured**. Repaired: correct path plus a hard failure when axe cannot be loaded. | `evidence/rc026-r2/playwright/playwright-report.json` (7 × "axe.min.js not found … skipping accessibility scan"); `tests/e2e/axe-helper.js:22-35` (pre-fix) |
| 13 | No .webm files | Confirmed. | repository scan |

---

## Gate summary after correction

| Gate | Status |
|------|--------|
| Playwright suite | Re-run required after repair; see the convergence evidence for the recorded result |
| Accessibility (axe) | Was **unmeasured**; axe now loads from the correct path and a load failure fails the suite |
| Pytest | Not affected by this branch (no Python source or test files changed); the 1087 figure is stale relative to current main |
| Ruff / Mypy / Build | Not affected by this branch |
| Installed-wheel import | Verified by the harness (site-packages assertion) |
| Legacy spec | Archived; browser-level replacement was **partial**. Contracts remain covered by Python integration tests |

---

## Verdict

```text
APPROVED (original, 2026-08-05) — WITHDRAWN
REQUEST_CHANGES — 2026-10-10 independent re-review
Repaired before merge; see docs/reports/RC026-R2-1-convergence-repair.md
```
