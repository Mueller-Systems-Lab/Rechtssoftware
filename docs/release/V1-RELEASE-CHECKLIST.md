# V1.0 Release Checklist — PrivateLegalNavigator

**Version:** v1.0.0-rc.3
**Corrected:** 2026-10-11 (measured values; inherited verdicts removed)
**Branch:** `release/rc3-readiness`

> **Correction notice.** This document previously carried the rc2-era verdict
> checklist forward while only its version strings were updated: it claimed
> "1021/1021 tests pass", a built Windows ZIP, a README updated with 1021 tests,
> and six PowerShell gates as `PASS` — none of which was true for this candidate.
> Every row below now states what was actually measured, and rows that were never
> executed say so. A PASS that cannot be reproduced is worse than an open gate,
> because it hides work instead of tracking it.

## Pre-Release Gates (Linux, local)

| # | Gate | Status | Evidence (measured) |
|---|------|--------|---------------------|
| 1 | Test suite | ✅ PASS* | 1398 collected → **1393 passed, 4 Frozen-RED (historical, by design), 1 documented skip**. The 4 failures are pre-fix contract evidence, unchanged. |
| 2 | Coverage ≥ 71 % baseline | ✅ PASS | **79 %** overall; both shipped packages measured |
| 3 | Ruff clean | ✅ PASS | `ruff check src tests` → All checks passed |
| 4 | Mypy strict clean | ✅ PASS | `mypy src` → no issues in 88 source files |
| 5 | pip check | ✅ PASS | `uv pip check` → all installed packages compatible |
| 6 | Wheel build | ✅ PASS | `python -m build` from the candidate commit |
| 7 | sdist build | ✅ PASS | same command; artifact hashes recorded in `release-readiness/final-gate-matrix.json` |
| 8 | twine check | ✅ PASS | wheel + sdist |
| 9 | CLI entry point | ✅ PASS | `private-legal-navigator --version` → `1.0.0rc3` |
| 10 | Runtime assets in wheel | ✅ PASS | 15 app templates, 1 BescheidPilot template, 5 demo fixtures, CSS + JS + SVG (verified by wheel inspection) |
| 11 | Cross-case isolation | ✅ PASS | 10 browser tests + API tests |
| 12 | Security surface exercised | ✅ PASS (author's own) | `release-readiness/security-review.md`; an independent review is a separate gate (see 40) |
| 13 | Version consistency | ✅ PASS | pyproject = `__version__` = CLI = FastAPI = Windows scripts = user docs = README = CHANGELOG |
| 14 | `backup_helper.py` ≥ 90 % | ✅ PASS | 92.9 % |
| 15 | `restore_helper.py` ≥ 90 % | ✅ PASS | 92.8 % |
| 16 | Installed-wheel E2E | ✅ PASS | clean venv, imports verified from `site-packages`, headed browser journey |
| 17 | Headed golden user journey | ⚠️ PARTIAL | 18/19 steps; the missing step needs a legal-source corpus (explicit GII sync) which this release does not perform |

\* "PASS" here means *no unexpected failure*: the only failures are the four
documented historical Frozen-RED tests.

## Release Artifact Gates

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 18 | Windows ZIP built | ❌ BLOCKED | No ZIP exists. `release/output/` is gitignored and **no script in the repository builds it** — the artifact was assembled by hand in an earlier cycle. See `release-readiness/windows-evidence.md`. |
| 19 | SHA256SUMS.txt | ❌ BLOCKED | depends on 18 |
| 20 | RELEASE-NOTES for the release output | ❌ BLOCKED | depends on 18; the in-repo `CHANGELOG.md` entry exists |
| 21 | INSTALLATION-KURZANLEITUNG.txt | ❌ BLOCKED | depends on 18 |

## Documentation Gates

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 22 | V1-DEFINITION-OF-DONE.md | ✅ PRESENT | `docs/release/`; its Windows §6 requirement is gate 23 |
| 23 | `docs/user/*` (install, first start, guide, backup, upgrade, uninstall, troubleshooting, known limitations) | ✅ PRESENT | version strings updated to rc.3 |
| 24 | README truth mirror | ✅ PASS | 1398 collected, 1393 passing, 4 Frozen-RED, 1 skip, 79 % |
| 25 | CHANGELOG updated | ✅ PASS | v1.0.0-rc.3 entry |
| 26 | `sync_service.py` coverage | ✅ PASS | measured **83.6 %** (the previously documented 77 % is stale) |

## Windows Script Gates

None of these can be marked PASS from Linux. They are **NOT EXECUTED**, not
verified: PowerShell execution policy, `%LOCALAPPDATA%` paths, `Get-FileHash`,
`Compress-Archive` and ZIP extraction behave differently on Windows, and the
scripts were only inspected statically.

| # | Gate | Status |
|---|------|--------|
| 27 | `install.ps1` (idempotent, no admin) | ⛔ NOT EXECUTED |
| 28 | `start.ps1` (healthcheck, browser) | ⛔ NOT EXECUTED |
| 29 | `stop.ps1` (own process only) | ⛔ NOT EXECUTED |
| 30 | `backup.ps1` (SHA-256 manifest) | ⛔ NOT EXECUTED |
| 31 | `restore.ps1` (integrity validation) | ⛔ NOT EXECUTED |
| 32 | `uninstall.ps1` (keep data / purge) | ⛔ NOT EXECUTED |

Additional known gap: `start.ps1` still exposes a `-HostAddr` parameter. Since
non-loopback binding is now refused with exit code 2, passing a non-loopback
address there fails closed — the parameter should be removed so the script cannot
offer an option the application rejects.

## GitHub Completion Gates

| # | Gate | Status |
|---|------|--------|
| 33 | Branch pushed | ⬜ TODO (this run) |
| 34 | PR created and reviewed | ⬜ TODO (this run) |
| 35 | Independent review of the integration | ⬜ TODO (this run) |
| 36 | Git tag `v1.0.0-rc.3` | 🔒 OWNER GATE |
| 37 | GitHub Release | 🔒 OWNER GATE |

## Final Classification

**AMBER_WINDOWS_COLD_TEST_REQUIRED** — all Linux-local gates that can be closed
are closed. The mandatory Windows cold install (Definition of Done §6) has never
been executed and no Windows environment is reachable, so this remains a release
**candidate** and not a release. Tagging and publishing stay with the owner.
