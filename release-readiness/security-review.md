# Security Review — v1.0.0-rc.3

Scope: the network surface, the case-data surface, the backup/restore path and
the legal-source path, as they behave in this candidate. Every claim below was
executed against a running instance or the installed wheel; nothing is inferred
from reading the source alone. Synthetic `SYNTHETISCH –` data only.

---

## 1. Verified controls

| Control | Test performed | Result |
|---------|----------------|--------|
| CSRF on user-facing forms | `POST /ui/cases/create` with no CSRF token | **403** |
| CSRF in a real browser | E2E `POST-without-CSRF-returns-403`, token read from the rendered form and submitted via `fetch` | pass |
| CSRF nonce cookie | asserted value, `HttpOnly`, `SameSite=Strict`, `path=/ui` on the form route that issues it | pass |
| Host validation on the UI surface | `GET /ui/cases` with `Host: evil.example` | **400** |
| Content Security Policy | `GET /` response headers | `default-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'` |
| Other security headers | same response | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` |
| No external resources | E2E asserts zero requests to non-loopback hosts and no external assets | pass |
| Safe XML parsing | `src/private_legal_navigator/infrastructure/safe_xml_parser.py` | `resolve_entities=False` for **all** parsers, `no_network=True` (blocks remote DTD/entity fetching); documented against CVE-2026-41066 |
| Path traversal in file storage | E2E cross-case probes; `restore_helper` traversal and symlink tests | pass |
| Path traversal in the BescheidPilot demo | `GET /demo-fixture/../etc/passwd` from an installed wheel | **404** |
| Cross-case isolation | 10 E2E tests: case A data unreachable via case B URLs at both UI and API level, sequential-ID probing returns 404 | pass |
| Error responses do not leak internals | E2E: no local file paths, no database details, no stack traces in error HTML or JSON | pass |
| Upload limits | E2E `413` oversized body, `415` wrong content type | pass |
| Sensitive logging | `tests/integration/test_uvicorn_access_log_privacy.py`, `test_event_logging_privacy.py`, `test_exception_boundary.py` | pass (in suite) |
| Backup integrity | `restore_helper` tests: SHA-256 verification, manipulated-backup detection, safe restore that refuses to overwrite silently | pass (in suite) |
| Non-loopback binding | `PLN_HOST=0.0.0.0` without opt-in | **refused**, clear error, exit code 2 |

## 2. The finding that motivated the binding change

Before this candidate, `PLN_HOST=0.0.0.0` started the server on all interfaces and
the case API answered over the LAN:

```
$ PLN_HOST=0.0.0.0 … serve
LISTEN  0  2048  0.0.0.0:18471  0.0.0.0:*
$ curl http://192.168.1.210:18471/api/v1/cases
{"items":[],"count":0}         # HTTP 200, unauthenticated
$ curl -H 'Host: 127.0.0.1:18471' http://192.168.1.210:18471/api/v1/cases
{"items":[],"count":0}         # HTTP 200 — spoofed Host also accepted
```

There is no authentication anywhere in the application, so this was full
unauthenticated access to case data for anything that could route to the host.
The Host-header allowlist did not prevent it, and could not: a caller chooses the
Host header, so it is not an access control.

**Change:** `Settings.__post_init__` now refuses a non-loopback bind unless
`PLN_ALLOW_NON_LOOPBACK=1` is set deliberately, with the refusal reported as a
clear message and exit code 2 rather than a traceback. Ten tests cover it,
including a subprocess test asserting the CLI refuses cleanly.

## 3. Accepted risks, deliberately

### 3.1 The JSON API carries no CSRF or Origin layer

`POST /api/v1/cases` without a CSRF token or `Origin` header returns **201**. This
is the API's design: the CSRF and Origin dependencies are attached to the `/ui/*`
routes, and the API is protected by being loopback-only.

Why this is acceptable: the application sets no session or authentication cookie
that a browser would attach automatically, and the API requires
`Content-Type: application/json`, so a cross-site "simple request" cannot reach it
without a CORS preflight that the application does not grant. There is therefore
no cross-site request forgery vector to defend against on this surface.

Why it is recorded anyway: if the API ever gains cookie-based authentication, or
if a browser extension or local process is considered in scope, this becomes a
gap. The `/api/v1/*` routes also have no Host validation
(`HostValidationMiddleware` guards `/ui/*` only). See `known-limitations.md` §8.

### 3.2 The opt-in escape hatch

`PLN_ALLOW_NON_LOOPBACK=1` allows a non-loopback bind with a stderr warning. The
constitution requires an explicit, documented decision for any deviation from
local-only processing, so an explicit opt-in is the correct shape — but it means
the control is a guard rail rather than a sandbox: whoever can set that variable
and restart the process can expose the API. Anyone who does so should record the
authorising decision in `PLN_ALLOW_NON_LOOPBACK_REASON` and treat the host as
hostile.

### 3.3 No request-body limit on the JSON API

The UI upload path enforces the 20 MB cap; `document_routes.py` on `/api/v1/*`
does not. Found by the swarm arm of this project's benchmark. Impact is bounded by
the loopback-only bind and the absence of authentication — a local process could
exhaust disk or memory, but cannot reach the API from off-host — so it is recorded
as an open resource-exhaustion gap rather than a data-exposure one.

### 3.4 No authentication

By design: a single-user, local-only desktop application. Every control above
assumes the loopback boundary holds.

## 4. Legal-source path (GII)

- HTTPS only, narrow host allowlist, redirect validation, SHA-256 snapshot
  integrity and `no_network` XML parsing are implemented in
  `infrastructure/safe_source_client.py` and `safe_xml_parser.py`.
- **No live, destructive GII apply was executed** during this release work. The
  legal-source behaviour exercised in the suite uses deterministic fixtures and
  the repository's own sync tests.
- Legal-source synchronisation remains strictly separated from case processing,
  and no scheduler or background sync exists.

## 5. What this review did not do

- No penetration test of the Windows PowerShell scripts (no Windows host).
- No fuzzing of the PDF extraction path beyond the malformed-PDF and
  oversized-upload cases in the suite.
- No independent third-party review; this is the author's own evidence, and the
  release mission requires a separate reviewer for the final integration.
