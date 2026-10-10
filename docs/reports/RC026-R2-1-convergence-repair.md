# RC-026-R2.1 Convergence Repair Record

**Date:** 2026-10-10
**Branch:** `test/rc026-playwright-e2e-closure` (converged onto current `main`)
**Convergence merge commit:** `68c5568` — merges `39cc098` (`main`, 2026-08-28) into `0a8aa52` (PR #13 head, based on `a26968b`)
**Scope:** repair of defects found by independent re-review during Merge-First convergence

---

## 1. Why this branch needed repair

PR #13 ("test: close remaining Playwright V1 E2E gates") was written against
`a26968b`, which predates both the BescheidPilot modular import (`9834db4`,
PR #15) and the brand/metadata commits (PR #18, #19). The merge itself was clean
(no conflicts), but the branch carried a set of PASS claims that its own
committed evidence contradicted.

**Verification that the merge cannot affect the Python suite:** the complete
diff against `main` contains no changes to any `.py` file under `src/` or
`tests/`, and `pytest --collect-only` reports the same 1091 tests before and
after the merge. The branch therefore cannot regress the Python suite; this was
verified mechanically rather than assumed.

## 2. Defects found and repaired

| # | Severity | Defect | Repair |
|---|----------|--------|--------|
| 1 | **P0** | `tests/e2e/axe-helper.js` resolved axe to `tests/src/private_legal_navigator/presentation/static/axe.min.js`, which does not exist. On miss it logged a warning and returned `{violations: []}`, so **every axe assertion passed vacuously and the accessibility gate was never measured** — while the evaluation contract claimed "0 axe critical, 0 axe serious". The branch's own committed report contains the skip warning 7 times. | Corrected the path to the repository root (`../../src/...`) and replaced the silent fallback with a hard failure: a missing axe file now fails the suite instead of reporting a clean scan. |
| 2 | **P1** | `tests/e2e/idempotency.spec.js` asserted `expect(successCount).toBeGreaterThanOrEqual(0)` — true for any count, so it could never fail. The test is named "10 rapid POSTs produce at most 1 record with the same title" but never asserted that. | Replaced with a real assertion: at most one of the ten identical POSTs may be accepted (single-use form CSRF token), and exactly one case with that title must exist. |
| 3 | **P1** | `tests/e2e/idempotency.spec.js` generated case titles as `E2E-IDEM-…`, violating the mandatory project rule that synthetic test data begins with `SYNTHETISCH –`. The titles were submitted through the real UI, creating records indistinguishable from user data. | Prefix enforced in `syntheticTitle()`. |
| 4 | **P1** | `tests/e2e/error-states.spec.js` "409 — idempotency key conflict" performed no request and no assertion; it was reported as passing. | Converted to `test.fixme` with a written reason. The application's real 409 semantics live on the M6-A expected-state-binding / idempotency-key routes, not on case creation; the browser flow that would exercise them is documented in the test and the gap is now visible instead of silently green. |
| 5 | **P1** | `tests/e2e/security-privacy.spec.js` CSRF-cookie test loaded `/ui/cases`, which by design sets no cookie, then returned early without asserting when no cookie was found. It could never fail. | Rewritten to load `/ui/cases/create` — the route that actually issues `pln_csrf_nonce` (`api/ui_routes.py:143-175`) — and to assert value, `HttpOnly`, `SameSite=Strict` and `path=/ui`. |
| 6 | **P1** | Silently-passing tests: `legal-timeline.spec.js` returned early when the seeded case was missing and wrapped its assertions in `if (timelineLink.count() > 0)`; `golden-path.spec.js` counted into an unused variable on the case page (candidates are not rendered there at all) and wrapped its document assertion in `if (count > 0)`. | All converted to unconditional assertions against elements the templates always render. The candidate/deadline test now navigates to the document page, where `documents/detail.html` renders the "Datums- und Zeitraumhinweise" section. |
| 7 | **P1** | `golden-path.spec.js` used the title `SYNTHETISCH E2E Form Test`, missing the mandatory en dash. | Corrected to `SYNTHETISCH – E2E Form Test`. |
| 8 | **P1** | Documentation claimed all 14 archived legacy browser tests were "fully replaced". In fact 9 were not: calculation preview form/result/trace, revoked-state preview, three viewport checks and two axe scans had no browser coverage. | `docs/reports/RC026-R2-1-legacy-spec-reconciliation.md` rewritten with an accurate mapping that distinguishes browser-level replacement from contract-level coverage, and names the Python integration tests that still cover the preview and revoked-state contracts. The three viewport checks are recorded as covered nowhere. |
| 9 | **P1** | `docs/reports/RC026-R2-1-independent-review.md` recorded `APPROVED` plus a green accessibility gate, "no tautologies" and "no relevant skips" — all three falsified by the branch's own evidence. | Rewritten as a corrected record: original content marked withdrawn, each item annotated with what was actually verified and the evidence for it. |
| 10 | **P2** | `playwright.config.js` wrote the JSON report to `evidence/rc026-r2/playwright/playwright-report.json`, a path that is both tracked in git and matched by `.gitignore`'s `/evidence/**/*.json` rule, so any local run silently overwrote committed audit evidence. | Reporter now writes to the gitignored `playwright-report/` directory. The existing committed report is retained as the historical record of the defective run and is labelled as such by the corrected documents. |
| 11 | **P2** | `package-lock.json` resolved all packages through `https://registry.npmmirror.com`, a third-party mirror, for a project with a strict no-external-dependency posture. | Normalized to `https://registry.npmjs.org` (5 occurrences). Content hashes are unchanged and remain verifiable. |
| 12 | **P2** | `docs/testing/PLAYWRIGHT-EVALUATION-CONTRACT.md` listed `restart_persistence` and `responsive_layout` as dimensions the suite satisfies; the suite only reloads the page and contains no viewport assertions. Its `KNOWN_FAILURE_CLASSES` also permitted "Test data not seeded → Skip with note, not fail", the loophole that made the vacuous tests possible. | Document corrected with a per-dimension status column; the skip-loophole class removed. |

## 3. What this branch does not fix

Recorded here so the gap is explicit rather than implied:

- **Browser coverage for the calculation preview** (form, result, deterministic
  trace, revoked state) and **the three mandatory viewports** is still absent
  from the browser suite. The preview and revoked-state contracts remain covered
  by `tests/integration/test_m6ui_slice4_calculation_preview.py`; the viewport
  checks are covered nowhere. Restoring the archived spec is not a drop-in move
  (it spawns its own server on fixed port 18000 and writes to a hardcoded
  evidence directory), so it is tracked as follow-up work.
- **Browser-level 409 for the stale-form contract** remains `fixme`; the
  contract is covered by `tests/integration/test_m6ui_slice3_correct_revoke.py`.
- The **"3 consecutive runs, 0 flaky"** claim is not reproducible from the
  repository and was not re-established here.

## 4. Verification performed

| Check | Method | Result |
|-------|--------|--------|
| Merge conflict-free | `git merge main` | clean |
| Python suite unaffected | diff contains no `.py` changes under `src/`/`tests/`; `pytest --collect-only` = 1091 on both sides | verified |
| axe path resolution | path now resolves to `src/private_legal_navigator/presentation/static/axe.min.js` (present, 553 KB) | verified |
| Browser suite | run against the converged tree with a headed browser; see the run record referenced below | see `playwright-report/` of the run |

## 5. Review status

The original `APPROVED` verdict was withdrawn on 2026-10-10 and the defects
above were repaired before merge. The repairs themselves require the same
independent review as any other change; the review of this record is part of the
convergence PR.
