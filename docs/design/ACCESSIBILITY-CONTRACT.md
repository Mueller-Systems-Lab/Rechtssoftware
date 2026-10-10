# Accessibility Contract — PrivateLegalNavigator v1.0.0rc2

**Date:** 2026-07-31
**Corrected:** 2026-10-10 (measured with axe-core against the installed wheel)
**Standard:** WCAG 2.2 Level AA target

## Current Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Skip to main content | PASS | `.skip-link` in base.html |
| Focus indicators | PASS | 3px outline with offset on `:focus-visible` |
| Semantic HTML landmarks | PASS | `<header role=banner>`, `<main>`, `<footer>`, `<nav>` |
| Heading hierarchy | PARTIAL | All pages have h1, but heading nesting varies |
| Form labels | PASS | All inputs have associated `<label>` |
| Error association | PASS | `.form-error-summary` with list + per-field errors |
| Color contrast (text) | **PASS (measured)** | see "Contrast measurement" below |
| Color contrast (status) | PASS (measured) | no status colour produced a critical/serious axe violation |
| Non-color indicators | PASS | Status badges include dot indicators, borders, and text |
| Keyboard navigation | PARTIAL | Tab order functional but no visible skip-to-section nav |
| Reduced motion | PASS | `prefers-reduced-motion: reduce` disables all transitions |
| Touch targets ≥44px | PASS | Buttons and form inputs have `min-height: 44px` |
| Print styles | PASS | Hides nav chrome, strips background colors |
| Screen reader text | PASS | `.u-visually-hidden` utility available |
| Language attribute | PASS | `<html lang="de">` |
| Viewport meta | PASS | `<meta name="viewport" content="width=device-width, initial-scale=1.0">` |
| No auto-playing content | PASS | No audio/video |

## Contrast measurement (2026-10-10)

The axe tests in `tests/e2e/accessibility.spec.js` previously never executed:
`tests/e2e/axe-helper.js` resolved axe-core from a path that does not exist and
returned an empty violation list on miss, so the gate passed vacuously. With the
path repaired, the first honest run found **serious `color-contrast` violations
on every release-path page** (home 8 nodes, case list 8, create case 3, error
page 4, case detail 3).

Cause: the CSS token `--color-text-muted` was implemented as `#a1a1aa`
(2.33:1–2.56:1 on the surface backgrounds), while `docs/design/DESIGN-TOKENS.md`
documents the same token as `#666666`. The implementation had drifted from the
documented token value.

| Token value | on `#ffffff` | on `#fafafa` | on `#f4f4f5` | Verdict |
|-------------|-------------:|-------------:|-------------:|---------|
| `#a1a1aa` (implemented before) | 2.56:1 | 2.46:1 | 2.33:1 | FAILS AA |
| `#666666` (documented, restored) | 5.74:1 | 5.50:1 | 5.22:1 | PASSES AA |

The token was restored to its documented value. After the fix the headed
installed-wheel run reports **104 passed, 1 skipped, 0 failed** with no axe
critical or serious violations on the release path.

## Gaps

- No ARIA live regions for dynamic content
- No heading-level skip navigation within pages
- No dialog focus trapping (no modals currently exist)
- No landmark labeling beyond role attributes
- Tables lack `scope` attributes on headers
- The archived legacy spec's axe scans of the calculation-preview pages are not
  executed (see `docs/reports/RC026-R2-1-legacy-spec-reconciliation.md`)

## Accessibility Testing Approach

- Axe automated scan per page — executed in `tests/e2e/accessibility.spec.js`
  and **fails the suite** when axe cannot be loaded, so the gate can never pass
  unmeasured again
- Manual keyboard-only navigation test
- Manual focus-order check
- Screen reader test (Orca on Linux)
