import unittest

from drive.utils.files import storage_key, get_s3_url, get_s3_key


class TestStorageHelpers(unittest.TestCase):
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
