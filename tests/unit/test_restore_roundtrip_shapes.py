"""Backup → restore round-trip shapes and manifest integrity (Gate K).

Three regressions are pinned here:

1. The flat archive layout restores (baseline behaviour).
2. The layout produced by ``release/windows/backup.ps1`` restores. That script
   uses ``Compress-Archive -Path <folder>``, which stores the folder as a single
   top-level entry, so the manifest ends up one level down. ``restore_backup``
   demanded it at the archive root, so the documented Windows backup→restore
   round-trip failed with "No backup-manifest.json found in backup".
3. A manifest that documents a payload file which is missing from the archive is
   a **hard error**. Skipping it let restore report success while a case pointed
   at a document that no longer existed — silent data loss.

All data is synthetic and carries the mandatory ``SYNTHETISCH –`` prefix.
"""

from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from private_legal_navigator.infrastructure.backup_helper import create_backup
from private_legal_navigator.infrastructure.restore_helper import restore_backup

SYNTH_TITLE = "SYNTHETISCH – Restore Round-Trip"
SYNTH_DOC = "SYNTHETISCH – KEINE ECHTEN PERSONENDATEN\nBescheid vom 15.06.2026\n".encode()


def _make_data_dir(tmp_path: Path, with_document: bool = False) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    conn = sqlite3.connect(data / "private_legal_navigator.db")
    try:
        conn.execute("CREATE TABLE cases (case_id TEXT PRIMARY KEY, title TEXT NOT NULL)")
        conn.execute("INSERT INTO cases VALUES (?, ?)", ("case-1", SYNTH_TITLE))
        conn.commit()
    finally:
        conn.close()
    if with_document:
        docs = data / "documents"
        docs.mkdir()
        (docs / "doc-1.txt").write_bytes(SYNTH_DOC)
    return data


def _make_backup(tmp_path: Path, with_document: bool = False) -> tuple[Path, Path]:
    data = _make_data_dir(tmp_path, with_document=with_document)
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    create_backup(data, backup_dir)
    return data, backup_dir


def _zip(backup_dir: Path, zip_path: Path, prefix: str) -> Path:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(backup_dir.rglob("*")):
            if path.is_file():
                zf.write(path, prefix + path.relative_to(backup_dir).as_posix())
    return zip_path


def _rewrite_manifest(zip_path: Path, mutate) -> Path:
    """Rewrite a zip, replacing backup-manifest.json with a mutated copy.

    The stored manifest hash is recomputed so the change is not masked by the
    hash check — that check is a different control from the one under test.
    """
    import hashlib

    out = zip_path.with_name("mutated-" + zip_path.name)
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info)
            if info.filename.endswith("backup-manifest.json"):
                manifest = json.loads(data)
                mutate(manifest)
                data = json.dumps(manifest, indent=2).encode("utf-8")
                manifest_digest = hashlib.sha256(data).hexdigest()
                # Keep any separately stored manifest hash consistent.
                for other in src.infolist():
                    if other.filename.endswith("backup-manifest.sha256"):
                        dst.writestr(other, manifest_digest)
                dst.writestr(info, data)
            else:
                dst.writestr(info, data)
    return out


def _titles(data_dir: Path) -> list[str]:
    conn = sqlite3.connect(data_dir / "private_legal_navigator.db")
    try:
        return [row[0] for row in conn.execute("SELECT title FROM cases").fetchall()]
    finally:
        conn.close()


def test_flat_layout_restores(tmp_path: Path) -> None:
    _, backup_dir = _make_backup(tmp_path)
    zip_path = _zip(backup_dir, tmp_path / "flat.zip", "")
    target = tmp_path / "target-flat"

    result = restore_backup(zip_path, target)

    assert result["status"] == "restored"
    assert _titles(target) == [SYNTH_TITLE]


def test_single_wrapper_dir_layout_restores(tmp_path: Path) -> None:
    """The shape produced by release/windows/backup.ps1 must restore."""
    _, backup_dir = _make_backup(tmp_path)
    zip_path = _zip(backup_dir, tmp_path / "wrapped.zip", "PrivateLegalNavigator-Backup/")
    target = tmp_path / "target-wrapped"

    result = restore_backup(zip_path, target)

    assert result["status"] == "restored"
    assert _titles(target) == [SYNTH_TITLE]
    # The wrapper directory must be unpacked, not recreated inside the target.
    assert not (target / "PrivateLegalNavigator-Backup").exists()


def test_flat_layout_with_document_roundtrips(tmp_path: Path) -> None:
    _, backup_dir = _make_backup(tmp_path, with_document=True)
    zip_path = _zip(backup_dir, tmp_path / "flat-doc.zip", "")
    target = tmp_path / "target-doc"

    restore_backup(zip_path, target)

    assert (target / "documents" / "doc-1.txt").read_bytes() == SYNTH_DOC


def test_missing_documented_document_is_a_hard_error(tmp_path: Path) -> None:
    """A manifest promising a file that is absent must fail, not silently pass."""
    _, backup_dir = _make_backup(tmp_path, with_document=True)
    zip_path = _zip(backup_dir, tmp_path / "missing-doc.zip", "")

    # Drop the document payload but keep it documented in the manifest.
    stripped = tmp_path / "missing-doc-stripped.zip"
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(
        stripped, "w", zipfile.ZIP_DEFLATED
    ) as dst:
        for info in src.infolist():
            if "documents/" in info.filename:
                continue
            dst.writestr(info, src.read(info))

    target = tmp_path / "target-missing-doc"
    with pytest.raises(ValueError, match="Missing file"):
        restore_backup(stripped, target)


def test_missing_documented_snapshot_is_a_hard_error(tmp_path: Path) -> None:
    """Same contract for legal-source snapshots."""
    data, backup_dir = _make_backup(tmp_path)
    snaps = data / "snapshots"
    snaps.mkdir()
    (snaps / "snap-1.xml").write_bytes(b"<law>SYNTHETISCH</law>")
    # Re-create the backup so the snapshot is documented, then build the zip.
    backup_dir2 = tmp_path / "backup2"
    backup_dir2.mkdir()
    create_backup(data, backup_dir2)
    zip_path = _zip(backup_dir2, tmp_path / "with-snap.zip", "")

    stripped = tmp_path / "no-snap.zip"
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(
        stripped, "w", zipfile.ZIP_DEFLATED
    ) as dst:
        for info in src.infolist():
            if "snapshots/" in info.filename:
                continue
            dst.writestr(info, src.read(info))

    with pytest.raises(ValueError, match="Missing file"):
        restore_backup(stripped, tmp_path / "target-no-snap")
