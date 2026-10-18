import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install_skill import install
from build_release import payload_files


class InstallChecks(unittest.TestCase):
    def test_installed_payload_matches_reviewed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "技能目录" / "ted-pre-master"
            result = install(destination)
            self.assertTrue(result["verified"])
            for source in payload_files(ROOT):
                self.assertEqual(source.read_bytes(), (destination / source.relative_to(ROOT)).read_bytes())
            self.assertFalse((destination / "evaluation").exists())

    def test_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            existing = destination / "SKILL.md"
            existing.write_text("Existing user skill", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                install(destination)
            self.assertEqual(existing.read_text(encoding="utf-8"), "Existing user skill")


if __name__ == "__main__":
    unittest.main()
