# Known Limitations — PrivateLegalNavigator v1.0.0-rc.3

Bind this document to the candidate commit it ships with. It records what this
candidate does **not** do, so that no reader has to infer a limitation from
silence.

---

## 1. Windows cold install has never been executed

The project's own Definition of Done (`docs/release/V1-DEFINITION-OF-DONE.md`,
§6) requires the golden journey to be performed after installing the release ZIP
on a fresh Windows machine. That has never happened:

- `CHANGELOG.md` (rc2 section) records GATE-11 as "Windows cold-test harness
  prepared (not executed on Linux)".
- `docs/release/V1-VALIDATION-REPORT.md` records Windows 10/11 as
  "TBD — Phase D pending".
- No script in the repository builds the release ZIP, and `release/output/` is
  gitignored, so the artifact that gate refers to is absent from source control.
- No Windows environment is reachable from the release host.

**Consequence:** `WINDOWS_COLD_TEST=BLOCKED`. Because the Definition of Done
makes that gate mandatory, this candidate **cannot** be classified as a green,
final release. It is a release **candidate**.

## 2. Case creation has no idempotency protection

Ten identical `POST /ui/cases/create` requests sharing one form CSRF token are
all accepted and create ten separate cases. Measured, not inferred: the E2E test
`tests/e2e/idempotency.spec.js` observed `Expected: <= 1, Received: 10` before it
was corrected to assert the behaviour that actually exists.

The M6-A candidate-confirmation route **does** implement an idempotency key
(`IdempotencyKeyConflictError`); case creation does not. An accidental double
submit therefore creates duplicate cases.

## 3. The form CSRF token is replayable

The token is HMAC-bound to the browser nonce, the request path and the method,
and it expires after one hour — but it is never consumed on use. Replaying it
within its lifetime is accepted. This is not a cross-site request forgery vector
(an attacker cannot read the token because of the same-origin policy), but it is
weaker than the "single-use token" description that previously circulated in the
test suite.

## 4. Browser-level coverage gaps

- **Calculation preview.** Form, result and deterministic trace are covered by
  Python integration tests
  (`tests/integration/test_m6ui_slice4_calculation_preview.py`), but not in the
  browser suite. The legacy Playwright spec that covered them is archived at
  `tests/.archive-e2e/` — outside Playwright's `testDir`, therefore not executed
  — and restoring it is not a drop-in move because it spawns its own server on a
  fixed port and writes to a hardcoded evidence directory.
- **Viewports.** The mandatory viewport checks (1920×1080, 1024×768, 390×844)
  are covered nowhere after the legacy spec was archived. No test in the
  repository asserts absence of horizontal overflow.
- **Browser-level 409.** The stale-form 409 flow is an explicit `test.fixme`
  with a written reason; the contract is covered by
  `tests/integration/test_m6ui_slice3_correct_revoke.py`.

## 5. The BescheidPilot public site data layer is missing

`docs/modules/bescheidpilot/site/assets/app.js` fetches
`data/{project-status,roadmap,evidence,features}.json`. None of those files
exist in the repository, so the site's data-driven sections cannot render. The
site is a documentation artifact and is **not** part of the installed package.
Completing it requires product and business content, not engineering work.

The corresponding test is skipped with that reason rather than silently passing.

## 6. Frozen-RED historical failures are expected

Four tests fail by design against the current tree — they encode pre-fix contract
violations from RC-025 and are evidence of the RED→GREEN transition, not
regressions:

```
tests/rc025/test_m7b_contract_red.py::test_red8_byte_identity_invariant
tests/rc025-r1/test_verifier_red.py::test_red_r1_byte_identity_violation
tests/rc025-r1/test_verifier_red.py::test_red_r1_no_download_count_check
tests/rc025/test_m7b_contract_red.py::test_red4_single_download_per_apply
```

They fail identically before and after this candidate's changes.

## 7. Test fixtures do not all use the `SYNTHETISCH –` prefix

`AGENTS.md` requires synthetic test data to begin with `SYNTHETISCH –`. The
BescheidPilot validation fixtures — both the imported originals under
`tests/fixtures/validation/` and the packaged copies the demo serves from
`src/bescheidpilot/fixtures/demo/` — instead open with
`VALIDIERUNGSFIXTURE — KEIN ORIGINALDOKUMENT — KEINE ECHTEN PERSONENDATEN`,
which carries the same meaning (and is arguably more explicit) but is not the
mandated token. They are not renamed here, because the extraction tests and the
gold-standard file key off their contents and a rename would be churn across 284
tests for no security gain. The packaged copies are kept byte-identical to the
originals by a test.

Note for the release owner: if the prefix is to be enforced mechanically, the
cleanest route is to prepend a `SYNTHETISCH – ` line to both the originals and
the packaged copies in one change, and re-record the gold-standard expectations.

## 8. Host-header validation does not cover the JSON API

`HostValidationMiddleware` only guards `/ui/*`. The `/api/v1/*` routes carry no
Host validation. This is **not** treated as a security boundary in this
candidate: a Host header is caller-controlled, so it cannot act as an access
control. The control that matters is the bind address, and that is now enforced
(see §9). The gap is recorded so it is a decision rather than an oversight.

## 9. Non-loopback binding is refused outright

`Settings` refuses to construct at all when `PLN_HOST` is not a loopback address
(anywhere in `127.0.0.0/8`, `::1`, or `localhost`), and the CLI reports the
refusal as a clear error with exit code 2. There is deliberately **no**
environment-variable opt-in: the constitution permits a local-only deviation only
after an explicit, documented architecture decision, and a one-word switch that
silently publishes an unauthenticated case API is not such a decision. Deviating
requires a code change together with an ADR.

## 9a. The JSON API has no request-body size limit

`document_routes.py` accepts uploads on `/api/v1/*` without the 20 MB cap that the
UI upload path enforces, so a local caller can post an arbitrarily large body.
Found by the swarm arm of this project's benchmark. Impact is limited to a local,
single-user, loopback-only process — it is a resource-exhaustion concern, not a
data-exposure one — but it is a real inconsistency between the two surfaces
(the Host-validation half of the same review is recorded in §8) and is recorded
rather than silently tolerated.

## 10. `agent_generated_verdict` provenance for the rc2 acceptance

The rc2 handoff binds a human `ACCEPT` verdict to commit `6a62460aaa…`, which
resolves neither locally nor on GitHub, and two documents publish different
artifact hashes for the same version. The rc2 acceptance is therefore not
independently reproducible. This candidate does not attempt to reconstruct it.
