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
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_s3_client_still_requires_s3_dependencies_when_enabled(self):
        script = """
import builtins
import importlib
import sys
import types
from types import SimpleNamespace

real_import = builtins.__import__

def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "boto3" or name.startswith("botocore"):
        raise ImportError(name)
    return real_import(name, globals, locals, fromlist, level)

frappe = types.ModuleType("frappe")
frappe.qb = SimpleNamespace(DocType=lambda name: SimpleNamespace(modified="modified"))
frappe.whitelist = lambda *a, **k: (lambda f: f)
frappe.session = SimpleNamespace(user="Guest")
frappe.db = SimpleNamespace(escape=lambda x: x, sql=lambda *a, **k: [], get_list=lambda *a, **k: [], get_value=lambda *a, **k: None)
frappe.get_all = lambda *a, **k: []
frappe.get_doc = lambda *a, **k: None
frappe.get_value = lambda *a, **k: None
frappe.get_site_path = lambda *a: "/tmp"
frappe.utils = SimpleNamespace(now=lambda: None, now_datetime=lambda: None)
frappe.throw = lambda *a, **k: (_ for _ in ()).throw(Exception("frappe.throw called"))
frappe.log_error = lambda *a, **k: None
frappe.get_single = lambda *a, **k: SimpleNamespace(
    enabled=True,
    flat=False,
    bucket="bucket",
    aws_key="key",
    endpoint_url="",
    signature_version="s3v4",
    get_password=lambda field: "secret",
)
sys.modules["frappe"] = frappe

pypika = types.ModuleType("pypika")
pypika.Field = lambda name: name
pypika.functions = SimpleNamespace(Coalesce=lambda *a, **k: SimpleNamespace(as_=lambda alias: alias))
sys.modules["pypika"] = pypika

mimemapper = types.ModuleType("mimemapper")
mimemapper.get_mime_type = lambda *a, **k: "application/octet-stream"
sys.modules["mimemapper"] = mimemapper

PIL = types.ModuleType("PIL")
PIL.Image = SimpleNamespace(frombytes=lambda *a, **k: None, open=lambda *a, **k: None)
PIL.ImageOps = SimpleNamespace(exif_transpose=lambda image: image)
sys.modules["PIL"] = PIL

locks = types.ModuleType("drive.locks.distributed_lock")
class DistributedLock:
    def __init__(self, *a, **k):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
locks.DistributedLock = DistributedLock
sys.modules["drive.locks.distributed_lock"] = locks

builtins.__import__ = fake_import
module = importlib.import_module("drive.utils.files")
try:
    module.FileManager()
except ImportError as exc:
    assert str(exc) in {"boto3", "botocore.config"}
else:
    raise AssertionError("Expected ImportError when S3 client is created")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            timeout=10,
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
