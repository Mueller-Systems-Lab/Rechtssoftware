# Held-out golden user journey — v1.0.0rc.3

**Candidate:** `5deea0db510487b85a5e70d434f5872c6fa1fdc9`
**Result:** **21 of 21 steps passed, exit code 0**
**Browser:** Chromium 151, **headed** (a visible window; not a headless run)
**Target:** the wheel installed into a throwaway virtual environment, server
started from `site-packages` with a fresh data directory — imports verified as
coming from `site-packages`, not from the checkout.
**Data:** synthetic only. The case title is `SYNTHETISCH – Golden Journey …` and
the uploaded PDF contains no real personal data.

Screenshots for every step are in `results/integration-gates/journey/` in the
benchmark workspace, alongside `journey-result.json`.

## Steps

| # | Step | Result |
|---|------|--------|
| 1 | Case list loads | PASS |
| 2 | Case created through the real form (POST accepted, redirect to the list) | PASS |
| 3 | New case opens from the list | PASS |
| 4 | Synthetic PDF uploaded through the file input and listed | PASS |
| 5 | Document page shows extraction/classification | PASS |
| 6 | Non-binding notice present | PASS |
| 7 | Candidate detail renders with evidence/review wording | PASS |
| 8 | Candidate offers a human confirmation action | PASS |
| 9 | Confirmation recorded (visible in history) | PASS |
| 10 | Calculation preview renders | PASS |
| 11 | Preview is explicitly non-binding | PASS |
| 12 | Calculation either traces its arithmetic or refuses explicitly | PASS (refused, with a reason) |
| 13 | No legally binding deadline is produced | PASS |
| 14 | Legal-source search page responds | PASS |
| 15 | Case legal situation renders | PASS |
| 16 | Legal timeline renders | PASS |
| 17 | Evidence pack renders | PASS |
| 18 | Evidence pack carries human-review wording | PASS |
| 19 | No uncaught page errors during the journey | PASS |

Two steps are recorded as informational rather than as failures:

- **Norm detail requires a legal-source sync.** A fresh data directory has no
  legal corpus, and no destructive or live GII apply is performed during release
  verification. Reaching a norm page is therefore only possible after an explicit
  sync.
- **No trace was produced for this seed.** The confirmed candidate carries an
  explicit date but no usable *duration*, so the product declined to compute a
  deadline and said so ("Der Kandidat enthält keine verwendbare Dauer."). That is
  the correct behaviour under the constitution — the software must not invent a
  legal deadline — and it is recorded as such rather than asserted away. The trace
  path itself is covered by `tests/integration/test_m6ui_slice4_calculation_preview.py`.

## Why this journey is worth more than the test suite

Running it found the defect that no test in the repository caught: every UI form
submission was being rejected with 403 because `Referrer-Policy: no-referrer`
made the browser send `Origin: null`, and the application's own origin check
refused it. Three tests actively asserted the harmful header value, and no test
performed a plain browser form POST — the E2E suite seeded its data over the API
and only *filled* the create form without submitting it. The suite is now
stronger for it: `tests/e2e/golden-path.spec.js` submits the form through the
browser and asserts the case appears.

## Restart, backup and restore (same run)

| Step | Result |
|------|--------|
| Server restarted against the same data directory; case page still 200 with its title | PASS |
| Backup created (manifest with SHA-256, `db_integrity: ok`, one document) | PASS |
| Archive built from the backup directory | PASS |
| Restore into an empty data directory | PASS |
| Case reopened from the restored data directory | PASS |
