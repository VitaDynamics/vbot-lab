"""Dependency-bundle checks; never execute Bazel or contact a device."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("offline", ROOT / "tools/bazel_offline.py")
offline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(offline)


class OfflineBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name).resolve()
        self.file = self.bundle / "vendor/VENDOR.bazel"
        self.file.parent.mkdir()
        self.file.write_text('ignore("@@platforms~host_platform~host_platform")\n')
        self.manifest = {"bazel": "7.6.1", "module_sha256": offline.digest(ROOT / "MODULE.bazel"),
                         "lock_sha256": offline.digest(ROOT / "MODULE.bazel.lock"),
                         "files": {"vendor/VENDOR.bazel": offline.digest(self.file)}}
        self.write_manifest()

    def write_manifest(self):
        (self.bundle / "manifest.json").write_text(json.dumps(self.manifest))

    def test_valid(self):
        offline.verify(self.bundle)

    def test_changed_file(self):
        self.file.write_text("changed")
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_unlisted_file(self):
        (self.file.parent / "unexpected.bzl").write_text("unexpected input")
        with self.assertRaisesRegex(ValueError, "inventory changed"):
            offline.verify(self.bundle)

    def test_wrong_checkout(self):
        self.manifest["lock_sha256"] = "0" * 64
        self.write_manifest()
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_escape(self):
        self.manifest["files"] = {"../outside": "0" * 64}
        self.write_manifest()
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_symlink(self):
        (self.file.parent / "link").symlink_to(self.file)
        self.manifest["files"]["vendor/link"] = offline.digest(self.file)
        self.write_manifest()
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_missing_bundle_never_starts_bazel(self):
        with patch("sys.argv", ["offline", "--bundle", str(self.bundle / "missing"),
                                "--output-user-root", str(self.bundle / "out"), "build", "//recipes/..."]):
            with patch.object(offline.subprocess, "check_output") as execute:
                with self.assertRaises(FileNotFoundError):
                    offline.main()
                execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
