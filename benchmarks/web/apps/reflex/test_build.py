"""Keep frontend dependency pins in the canonical location consumed by Reflex."""

# ruff: noqa: PT009
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from build import seed_frontend_resolution
from reflex.utils import frontend_skeleton


class BuildTests(unittest.TestCase):
    def test_seed_resolution_survives_reflex_canonical_sync(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            frontend = root / "frontend"
            frontend.mkdir()
            (frontend / "bun.lock").write_text("reviewed dependency resolution")
            (frontend / "package.json").write_text('{"dependencies": {}}')
            web = root / ".web"
            web.mkdir()
            (web / "bun.lock").write_text("stale resolution")
            seed_frontend_resolution(root)
            # Exercise Reflex's real synchronization without changing the process directory.
            with (
                patch.object(frontend_skeleton, "get_web_dir", return_value=web),
                patch.object(
                    frontend_skeleton, "get_root_lockfile_path", side_effect=lambda name: root / "reflex.lock" / name
                ),
            ):
                frontend_skeleton.sync_root_lockfile_to_web("bun.lock")
            self.assertEqual((web / "bun.lock").read_bytes(), (frontend / "bun.lock").read_bytes())
            self.assertEqual(
                (root / "reflex.lock/package.json").read_bytes(), (frontend / "package.json").read_bytes()
            )


if __name__ == "__main__":
    unittest.main()
