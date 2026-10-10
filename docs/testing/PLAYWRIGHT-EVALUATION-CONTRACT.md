# RC-026-R2 Playwright Evaluation Contract

**Generated:** 2026-08-05
**Corrected:** 2026-10-10 (convergence re-review)

> **Correction notice (2026-10-10):** on convergence onto current `main` the
> committed evidence showed that three of the thresholds below were not actually
> met by the suite as it stood:
>
> - **accessibility** — `tests/e2e/axe-helper.js` resolved axe to a
>   non-existent path and returned `{violations: []}` on miss, so every axe
>   assertion passed vacuously. The gate was **unmeasured**, not green. The path
>   is fixed and a load failure now fails the suite.
> - **restart_persistence** — the suite only reloads the browser page; it never
>   restarts the server. Restart persistence is covered elsewhere
>   (`scripts/run-installed-wheel-e2e.py`), but not here. The dimension is
>   therefore not satisfied by this suite.
> - **Deterministic assertions / no tautologies** — the original review checked
>   only for `or True` and `catch-and-ignore` forms. It missed
>   `expect(count).toBeGreaterThanOrEqual(0)`, a tautology, and several tests
>   that asserted nothing at all by returning early or wrapping assertions in
>   `if (count > 0)`. Those are repaired in this branch.
>
> The `KNOWN_FAILURE_CLASSES` entry "Test data not seeded → Skip with note, not
> fail" has been removed: the harness always seeds its data, so a missing seed is
> a real failure. Skipping it made unmeasured gates look green.

---

## QUALITY_DIMENSIONS

| Dimension | Description | Threshold | Status on this branch |
|-----------|-------------|-----------|----------------------|
| functional_correctness | UI workflows produce correct results | 100% mandatory scenarios GREEN | asserted |
| browser_observability | No console errors, no page errors, no external requests | 0 unexpected errors | asserted |
| data_integrity | Data survives restart, no duplicate records | 0 data loss, 0 duplicate mutations | page reload only — see notice |
| security | CSP, CSRF, host validation, no secrets in DOM | 0 security violations | asserted (`/ui/*`; the JSON API carries no CSRF/host layer by design) |
| privacy | No case data in logs, no external assets, no telemetry | 0 privacy violations | asserted |
| accessibility | axe-core: no critical or serious violations | 0 critical, 0 serious | **unmeasured** until axe path repaired; now asserted |
| responsive_layout | No horizontal overflow at mandatory viewports | 0 overflow at 1920/1280/1024/390 | no viewport assertions in the new suite — see legacy reconciliation |
| restart_persistence | Data survives server restart | 0 data loss after restart | not covered by this suite |
| idempotency | Double submits produce no duplicate records | 0 duplicate mutations | asserted |
| current_historical_search_separation | Standard search shows only CURRENT | Must match ADR-010 behavior | asserted |
| release_installation_fidelity | Tests run against installed wheel, not source checkout | Import from site-packages only | asserted by harness |

## EVALUATION_DATASET

All data exclusively synthetic:
- Synthetic case: "SYNTHETISCH – Playwright E2E Testfall"
- Synthetic PDF: Generated via pymupdf with test text
- Synthetic deadline: "Bescheid vom 15.06.2026"
- No real names, no real case numbers, no production GII mutations

Every record created by the suite must carry the mandatory `SYNTHETISCH –`
prefix. Titles generated ad hoc (for example the idempotency fixtures, which
previously used `E2E-IDEM-…`) were a violation of this rule and are repaired.

## DETERMINISTIC_ASSERTIONS

- No `or True`, no tautologies — including count assertions of the form
  `toBeGreaterThanOrEqual(0)`
- No `catch-and-ignore` around assertion errors
- No assertions based solely on text length
- No critical actions bypassed via direct DB manipulation
- No test may pass by returning early: if a precondition is missing, the test
  fails rather than silently succeeding

## PASS_THRESHOLDS

```
100% mandatory scenarios GREEN
0 unexpected console errors
0 page errors
0 external requests (except gesetze-im-internet.de for GII)
0 axe critical
0 axe serious
0 horizontal overflow at mandatory viewports
0 duplicate mutations
0 data loss after restart
0 source-checkout imports
```

## KNOWN_FAILURE_CLASSES

| Class | Treatment |
|-------|-----------|
| GII live sync (no approval) | Skip, not execute |
| Firefox/WebKit unsupported | Skip with note (Chromium is mandatory) |
| axe moderate/minor violations | Log, not block |
| Browser-level contract with no implementation yet | `test.fixme` with a written reason — visible in the report, never a silent pass |

