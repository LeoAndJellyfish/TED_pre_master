import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_release", ROOT / "scripts/build_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class PackageChecks(unittest.TestCase):
    def test_archive_is_reproducible_and_matches_source(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first.zip", Path(directory) / "second.zip"
            self.assertEqual(release.build(ROOT, first)["sha256"], release.build(ROOT, second)["sha256"])
            with zipfile.ZipFile(first) as archive:
                for name in archive.namelist():
                    relative = Path(name).relative_to("ted-pre-master")
                    self.assertEqual(archive.read(name), (ROOT / relative).read_bytes())
                self.assertFalse(any("evaluation/" in name or "docs/" in name or ".git/" in name for name in archive.namelist()))

    def test_missing_required_file_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                release.payload_files(Path(directory))


if __name__ == "__main__":
    unittest.main()
