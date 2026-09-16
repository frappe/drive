from pathlib import Path
import subprocess
import sys
import unittest

from drive.utils.files import storage_key, get_s3_url, get_s3_key


class TestStorageHelpers(unittest.TestCase):
    def test_module_import_does_not_require_s3_dependencies(self):
        script = """
import builtins
import importlib

real_import = builtins.__import__

def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "boto3" or name.startswith("botocore"):
        raise ImportError(name)
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = fake_import
module = importlib.import_module("drive.utils.files")
assert module.get_s3_key("/files/test.txt") == "test.txt"
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_s3_url_roundtrip(self):
        # get_s3_url builds a stored file_url; storage_key must recover the key.
        for key in [
            "abc/def.png",
            "team one/sub folder/file name.pdf",
            "résumé/spaced key.txt",
            "a/b+c?d=e&f.bin",
        ]:
            self.assertEqual(storage_key(get_s3_url(key)), key)

    def test_storage_key_is_always_relative(self):
        # Never returns a leading slash, so `Path(base) / key` can't reset.
        for url in ["/private/files/x", "/files/y", "//z", "https://ext/u"]:
            self.assertFalse(storage_key(url).startswith("/"))

    def test_get_s3_key_strips_disk_prefix(self):
        self.assertEqual(get_s3_key("/private/files/a/b.png"), "a/b.png")
        self.assertEqual(get_s3_key("/files/a/b.png"), "a/b.png")
        # Already a bare key: unchanged.
        self.assertEqual(get_s3_key("a/b.png"), "a/b.png")
