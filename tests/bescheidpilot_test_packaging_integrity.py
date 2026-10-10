"""Packaging integrity for the imported BescheidPilot module.

The module is shipped as part of the distribution, so two things must hold:

1. Every runtime asset the module reads at import or request time is present in
   the package (the web demo page template and the synthetic demo documents).
   Before this test existed, the template and the demo fixtures were resolved
   relative to the repository, so an installed wheel served a 404 for the demo
   page and for every fixture endpoint.
2. The packaged demo documents stay byte-identical to the validation fixtures
   they derive from, so there is exactly one source of truth and no silent
   drift between what the demo shows and what the validation suite uses.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "bescheidpilot"
VALIDATION_DIR = REPO_ROOT / "tests" / "fixtures" / "validation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DemoAssetPackagingTests(unittest.TestCase):
    """Assets the shipped demo needs must live inside the package."""

    def test_web_demo_template_is_packaged(self) -> None:
        template = PACKAGE_ROOT / "web" / "templates" / "index.html"
        self.assertTrue(
            template.is_file(),
            f"web demo template missing from the package: {template}",
        )

    def test_demo_fixture_directory_is_inside_the_package(self) -> None:
        from bescheidpilot.web.server import _FIXTURES_DIR

        resolved = Path(_FIXTURES_DIR).resolve()
        package = PACKAGE_ROOT.resolve()
        self.assertTrue(
            str(resolved).startswith(str(package)),
            f"demo fixtures must resolve inside the package, got {resolved}",
        )
        self.assertNotIn(
            "tests",
            resolved.parts,
            "demo fixtures must not resolve into the test tree; that only works "
            "in a source checkout and breaks from an installed wheel",
        )

    def test_every_allowlisted_demo_fixture_exists_and_is_synthetic(self) -> None:
        from bescheidpilot.web.server import DEMO_FIXTURES

        self.assertTrue(DEMO_FIXTURES, "demo fixture allowlist must not be empty")
        for fixture_id, path in DEMO_FIXTURES.items():
            with self.subTest(fixture_id=fixture_id):
                self.assertTrue(path.is_file(), f"fixture missing: {path}")
                first_line = path.read_text(encoding="utf-8").splitlines()[0]
                self.assertIn(
                    "KEINE ECHTEN PERSONENDATEN",
                    first_line,
                    "demo fixtures must carry the no-real-personal-data banner",
                )

    def test_packaged_demo_fixtures_match_their_validation_source(self) -> None:
        """Exactly one source of truth: packaged copies must not drift."""
        from bescheidpilot.web.server import DEMO_FIXTURES

        checked = 0
        for fixture_id, packaged in DEMO_FIXTURES.items():
            source = VALIDATION_DIR / packaged.name
            with self.subTest(fixture_id=fixture_id):
                self.assertTrue(
                    source.is_file(),
                    f"validation source missing for demo fixture: {source}",
                )
                self.assertEqual(
                    _sha256(packaged),
                    _sha256(source),
                    f"packaged demo fixture drifted from {source.name}: "
                    "re-copy it so the demo and the validation suite stay identical",
                )
                checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
