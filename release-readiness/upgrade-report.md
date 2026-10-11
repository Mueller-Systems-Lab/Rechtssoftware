# Upgrade and data-integrity report — v1.0.0rc.3

**Candidate:** `5deea0db510487b85a5e70d434f5872c6fa1fdc9`

## 1. Upgrade from a previous release: NOT TESTED, and why

The project's Definition of Done asks for a previous-release data set to be
carried forward. That test **cannot be performed honestly here**, and pretending
otherwise would be the exact class of false evidence this candidate exists to
remove:

- `1.0.0rc.2` was **never tagged and never published**, so there is no released
  artifact a user could have installed;
- the commit its handoff records as user-accepted (`6a62460aaa…`) resolves neither
  locally (`git cat-file` → bad object) nor on GitHub (HTTP 422);
- the two documents that describe rc2's artifacts publish **different** wheel and
  sdist hashes for the same version, so no single rc2 artifact can be identified
  with confidence;
- `v1.0.0-rc.1` exists as a tag, but the branch that carried it
  (`release/v1-installable-closure`) was superseded and PR #11 was closed, so it
  is not a supported upgrade source either.

Recording `UPGRADE_FROM_PREVIOUS_RELEASE = NOT TESTED` is the truthful result.
It is not a green gate and is not presented as one.

## 2. What *is* verified about data integrity

| Property | Method | Result |
|----------|--------|--------|
| Schema initialisation is automatic and idempotent on startup | application start against an empty data directory, repeated | PASS |
| Data survives an application restart | create case → upload document → stop server → start again against the same data directory → case page returns 200 with its title | PASS |
| Backup produces a manifest with SHA-256 hashes and an integrity check | `python -m private_legal_navigator.infrastructure.backup_helper <data> <out>` | PASS (`db_integrity: ok`, 1 document recorded) |
| Restore into an **empty** data directory | `restore_helper <zip> <target> --force` then start against the target | PASS |
| Case is intact after restore | case page returns 200 with its title | PASS |
| Document payload survives the round-trip | document count and payload present after restore | PASS |
| A manipulated payload is rejected | existing hash-verification tests | PASS |
| A manifest documenting a **missing** file is a hard error | new tests (`tests/unit/test_restore_roundtrip_shapes.py`) | PASS |
| An archive whose manifest sits in a wrapper directory restores | new tests, reproducing the shape `release/windows/backup.ps1` produces | PASS |
| Append-only confirmation history | existing suite plus the browser journey's confirm step | PASS |

## 3. Two integrity defects fixed in this candidate

Both were found by the benchmark arms of this project and reproduced before being
accepted:

1. **The documented Windows backup → restore round-trip was broken.**
   `backup.ps1` uses `Compress-Archive -Path <folder>`, which stores the backup
   folder as a single top-level entry, while `restore_backup` required
   `backup-manifest.json` at the archive root. Restoring a Windows-produced
   backup failed with "No backup-manifest.json found in backup". `restore_backup`
   now resolves a single wrapper directory before validation and the atomic
   switch, and unpacks the content root so no stray subdirectory appears in the
   target.
2. **A restore could report success while data was missing.**
   A manifest entry that documents a payload file which is absent from the archive
   was silently skipped, so a case could be "restored" while pointing at a
   document that no longer existed. A missing documented document or snapshot is
   now a hard error.

Neither defect is reachable on the happy path the suite previously exercised,
which is why both survived until independent attempts looked at the restore path
from the outside.

## 4. Residual risk

- Migration between *future* versions is untested by construction: there is no
  released previous version to migrate from yet. The first upgrade that can be
  tested is the one from the first published release to the next one.
- The SQLite schema version is reported as `unknown` in backup manifests
  (`_get_schema_version` does not find a `user_version`). Restore therefore cannot
  refuse an incompatible schema on that basis; version incompatibility detection
  relies on the other manifest fields. Recorded as a known limitation.
