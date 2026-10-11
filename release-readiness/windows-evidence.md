# Windows Evidence — v1.0.0-rc.3

**Status: `WINDOWS_COLD_TEST=BLOCKED`**

## Requirement

`docs/release/V1-DEFINITION-OF-DONE.md` §6 makes this a MUST gate:

> Install from release ZIP on fresh Windows → create case → upload PDF → extract
> text → classify → detect deadlines → confirm reference date → show calculation
> preview → search legal source → link norm → create timeline event → export
> evidence pack → restart → data intact → create backup → restore in empty
> environment → re-open case

The same document's §2.5 requires the PowerShell pilot package to be exercised:
`install.ps1` (idempotent, no admin rights), `start.ps1` (loopback bind, opens
browser), `stop.ps1` (kills only its own process), `backup.ps1`, `restore.ps1`,
`uninstall.ps1` (keeps data by default, optional purge).

## Why it is blocked

No Windows 10/11 environment is reachable from the release host. The release host
runs CachyOS Linux; there is no Windows VM, no remote Windows host, and no
authorised route to one in this session.

Faking this gate from Linux — for example by running the golden journey on Linux
and reporting it as a Windows result — is explicitly prohibited by the release
mission, and would in any case be worthless: the things most likely to break are
exactly the things a Linux run cannot exercise (PowerShell execution policy,
`%LOCALAPPDATA%` paths, `Get-FileHash`, `Compress-Archive`, Python discovery,
browser launch, and the `.zip` extraction layout).

## What the project itself says

| Source | Statement |
|--------|-----------|
| `CHANGELOG.md` (rc2) | "GATE-11 Windows cold-test harness prepared (**not executed on Linux**)" |
| `docs/release/V1-VALIDATION-REPORT.md` §1 | `Windows 10/11 \| TBD \| ⏳ Phase D pending` |
| `docs/release/V1-RELEASE-CHECKLIST.md` | row 15 asserts the ZIP was built; no ZIP exists in the repository (`release/output/` is gitignored and no script builds it) |
| `git log --all -- release/output` | no committed ZIP |

So the project's own records agree that this gate has never been closed.

## What *can* be verified without Windows, and was

| Check | Method | Result |
|-------|--------|--------|
| PowerShell scripts are syntactically plausible and reference the current wheel name | static inspection of `release/windows/*.ps1` against the built wheel filename | consistent after the rc3 rename (`private_legal_navigator-1.0.0rc3-py3-none-any.whl`) |
| `install.ps1` pins the app version | `$AppVersion = "1.0.0rc3"` | matches `pyproject.toml` |
| Loopback binding on start | `start.ps1` passes the loopback host; the server now *refuses* non-loopback binds | enforced in code, not only by script default |
| Server-side behaviours the Windows scripts depend on (backup/restore/health) | exercised on Linux against the installed wheel | see `../docs/release/V1-RELEASE-CHECKLIST.md` rows 14–17 and the gate matrix at `results/integration-gates/final-gates-summary.txt` |

None of that substitutes for the gate. It is recorded so the reader knows exactly
which part is missing.

## Required to close

1. A Windows 10 or 11 machine (physical or VM) with no prior PrivateLegalNavigator
   installation.
2. The release ZIP built from the final candidate commit, by a script that is
   itself committed (today no such script exists).
3. `install.ps1` → `start.ps1` → golden journey → `stop.ps1` → `start.ps1` →
   `backup.ps1` → `restore.ps1` into an empty environment → `uninstall.ps1`
   (keep data) → optional purge, all on synthetic `SYNTHETISCH –` data.
4. A recorded transcript or screenshots bound to the candidate SHA.

Until then this candidate is a **release candidate**, not a release.
