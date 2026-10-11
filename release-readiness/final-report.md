# Release-Readiness Report — PrivateLegalNavigator v1.0.0rc.3

**Candidate commit (code):** `5deea0db510487b85a5e70d434f5872c6fa1fdc9`
**Baseline:** `479f14b` (current `main` after PR #13 was merged)
**Branch:** `release/rc3-readiness`
**Classification:** `AMBER_WINDOWS_COLD_TEST_REQUIRED`

> This candidate is a **release candidate**, not a release. Tagging and
> publishing are owner gates and were not performed. One mandatory gate in the
> project's own Definition of Done — the Windows cold install — has never been
> executed, so a green overall classification would be a false claim.

Machine-readable form: `final-gate-matrix.json`. Known limitations:
`known-limitations.md`. Windows: `windows-evidence.md`. Security:
`security-review.md`. Journey: `golden-journey.md`. Upgrade:
`upgrade-report.md`.

---

## 1. What this candidate changes

Six commits on top of the baseline. Each is a defect that was reproduced before
it was fixed; none is a refactor or a restyle.

### Release-truth repair

The previous candidate identity (`1.0.0rc.2`) is unresolvable: its recorded
user-accepted commit `6a62460aaa…` exists neither locally nor on GitHub, two
documents publish **different** artifact hashes for that version, and it was
never tagged although the Definition of Done requires the tag. Reusing that
identity for different bytes would be a false provenance claim, so this candidate
is `1.0.0rc.3`.

### Silent test collection (release blocker class: tests not collected)

`pyproject.toml` declared `python_files = "test_*.py"`, so all **284** imported
BescheidPilot tests (`tests/bescheidpilot_test_*.py`, ADR-021) were excluded from
the default suite. One was failing; one could never pass. Both patterns are
collected now: the suite reports **1400** tests instead of 1091.

### BescheidPilot shipped as code without its runtime assets

The wheel carried the module's Python but not `bescheidpilot/web/templates/index.html`,
so the demo page and every demo fixture endpoint returned 404 from an installed
wheel, and the fixtures resolved through `../../../tests/fixtures/validation`,
which only exists in a source checkout. Both are packaged now, with a test that
keeps the packaged copies byte-identical to their source and another that asserts
the packaging *declaration* rather than the file's existence.

### Local-only binding was defaulted, not enforced

`PLN_HOST=0.0.0.0` started the server on all interfaces and `/api/v1/cases`
answered with HTTP 200 over the LAN address (`192.168.1.210`), unauthenticated.
The application has no authentication and a Host header cannot act as an access
control, so the bind address is the only real boundary. Both the application and
the BescheidPilot demo server now **refuse** a non-loopback bind with exit code 2.
There is deliberately no environment-variable opt-in.

### Every UI form submission was rejected in Chromium

Found by the harness operator during the headed gate — **not** by either
benchmark arm, and actively *pinned* by three tests that asserted the harmful
value. With `Referrer-Policy: no-referrer`, Chromium sends `Origin: null` on
same-origin form POSTs (while `sec-fetch-site: same-origin`), and the
application's own origin check then rejected the request with 403
"Ungültige Anfrageherkunft". Creating a case, uploading a document and confirming
a candidate were all unusable in the browser. The policy is now `same-origin`;
the privacy property is unchanged because no referrer is ever sent cross-origin
and the CSP blocks cross-origin requests entirely.

### Harvested from this project's benchmark arms

Four defects were found by the two competing release-readiness attempts and
folded in after independent reproduction:

- the documented **Windows backup → restore round-trip** failed, because
  `backup.ps1` stores the backup folder as a wrapper entry while `restore_backup`
  demanded the manifest at the archive root;
- a **restore could report success while a manifest documented a missing
  document** — silent data loss;
- **`favicon.svg` was missing from the wheel** although `base.html` uses it as
  the icon and header image;
- the **sync lock lived in the process-global temp directory and was never
  released** (its release helper had no call site), so unrelated data directories
  collided and recovery depended on PID liveness — which misfires when a PID is
  recycled. This actually produced a false `SYNC_ALREADY_RUNNING` failure while
  this branch was being measured.

## 2. Verified state at this commit

| | Result |
|---|---|
| Test suite | **1400 collected → 1395 passed, 4 Frozen-RED (historical, by design), 1 documented skip**, 342 subtests, 60.6 s |
| Static quality | ruff clean; mypy strict clean (88 files); `uv pip check` clean |
| Coverage | **79 %** overall, measuring both shipped packages (`bescheidpilot` was previously invisible); backup 92.9 %, restore 92.8 %, sync 83.6 % |
| Build | wheel + sdist, `twine check` PASSED, hashes recorded |
| Installed wheel | clean venv, imports verified from `site-packages`, CLI `1.0.0rc3`, `/health` 200 |
| Headed golden journey | **21/21 steps, exit 0** — a visible Chromium walking the released UI against the installed wheel |
| Restart persistence | PASS |
| Backup → restore into an empty environment | PASS |
| Windows cold install | **BLOCKED** |

## 3. What is not verified — read this before releasing

1. **Windows.** Never executed. No ZIP exists, and no script in the repository
   builds one. Six PowerShell gates are marked `NOT EXECUTED`, not `PASS`.
2. **Upgrade from a previous release.** Cannot be exercised: there is no previous
   published release to upgrade from, because rc2 was never tagged or published
   and its recorded candidate commit is unresolvable. Automatic, idempotent schema
   initialisation on startup and restart persistence *are* verified.
3. **Legal-source sync against a live source.** Deliberately not executed; no
   destructive GII apply was performed. The safety properties (HTTPS-only, host
   allowlist, redirect validation, hash integrity, `no_network` XML parsing) are
   unchanged and covered by the existing suite.
4. **The calculation trace in the browser.** The journey's synthetic seed carries
   an explicit date but no usable duration, so the product correctly *refused* to
   compute a deadline rather than inventing one — which is the behaviour the
   constitution demands. The trace path itself is covered by Python integration
   tests, not by the browser journey.
5. **Recorded open defects**, deliberately not fixed here: no Host-validation
   layer or request-body limit on `/api/v1/*`; no idempotency protection on case
   creation; the form CSRF token is replayable for its lifetime; browser-level
   coverage of the calculation preview and the mandatory viewports is absent;
   the BescheidPilot public site's data layer was never imported.

## 4. Evidence provenance

Every PASS above binds to `5deea0d`. Nothing is inherited from an earlier
candidate: the documents that describe earlier candidates
(`V1-VALIDATION-REPORT.md` → `e54bb99`, `release/handoff/rc2-*` → the
unresolvable `6a62460`, `docs/reports/*`) each name their own commit and are left
as history. Two documents that had been *version-bumped while keeping their
rc2-era verdicts* — the release checklist and the security review — were
corrected rather than silently carried forward; that correction is itself part of
this candidate.

## 5. Review history

- `docs/reports/RC026-R2-1-independent-review.md` — the PR #13 review, verdict
  withdrawn and repaired.
- An independent review of *this* integration returned `REQUEST_CHANGES` with two
  P1 defects (an incomplete loopback refusal that still allowed the demo server to
  bind `0.0.0.0`, and documents describing an opt-in that no longer existed) plus
  four false PASS rows in the inherited release checklist. All P1 and P2 findings
  were fixed and re-verified; the fixes are the final commit before this report.
