import os
import tempfile
import unittest
from unittest import mock

from app.core import files
from app.core.files import UploadError, safe_filename, validate_source_upload


class FilenameTests(unittest.TestCase):
    def test_path_traversal_stripped(self):
        self.assertEqual(safe_filename("../../etc/passwd.py"), "passwd.py")
        self.assertEqual(safe_filename("..\\..\\win\\evil.py"), "evil.py")

    def test_rejects_empty_and_dots(self):
        for bad in ("", "..", "   ", "/"):
            with self.assertRaises(UploadError):
                safe_filename(bad)


class ValidationTests(unittest.TestCase):
    def test_accepts_python(self):
        name, text = validate_source_upload("a.py", b"print(1)\n")
        self.assertEqual((name, text), ("a.py", "print(1)\n"))

    def test_rejects_disallowed_extension(self):
        for bad in ("evil.exe", "x.zip", "noext", "a.py.exe"):
            with self.assertRaises(UploadError):
                validate_source_upload(bad, b"x")

    def test_rejects_oversize_empty_binary_and_non_utf8(self):
        with self.assertRaises(UploadError): validate_source_upload("a.py", b"x" * 20, max_bytes=10)
        with self.assertRaises(UploadError): validate_source_upload("a.py", b"  \n")
        with self.assertRaises(UploadError): validate_source_upload("a.py", b"a\x00b")
        with self.assertRaises(UploadError): validate_source_upload("a.py", b"\xff\xfe\xfa")


class StorageTests(unittest.TestCase):
    def test_store_read_delete_and_traversal_guard(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(files, "settings", mock.Mock(upload_dir=d, max_source_bytes=1000)):
                ref = files.store_source("hello")
                self.assertRegex(ref, r"^[0-9a-f]{32}\.src$")
                self.assertEqual(files.read_source(ref), "hello")
                self.assertIsNone(files.read_source("../../etc/passwd"))
                files.delete_source("../../etc/passwd")  # must not raise or touch anything
                files.delete_source(ref)
                self.assertFalse(os.path.exists(os.path.join(d, ref)))


if __name__ == "__main__":
    unittest.main()
