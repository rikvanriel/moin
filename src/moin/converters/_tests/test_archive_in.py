from io import BytesIO
import zipfile

import pytest

from moin.converters.archive_in import ArchiveException, ZipConverter


class TestZipConverter:
    def test_list_contents_valid_zip(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, mode="w") as zf:
            zf.writestr("example.txt", b"abcdefghij")
        rows = ZipConverter().list_contents(BytesIO(buf.getvalue()))
        assert [name for _, _, name in rows] == ["example.txt"]

    def test_list_contents_corrupt_zip_raises_archive_exception(self):
        # A defective zip must surface as ArchiveException rather than
        # leaking zipfile internals (BadZipFile/RuntimeError). This locks
        # the behavior of the corrupt-archive handler touched by the
        # BadZipFile compatibility fix.
        with pytest.raises(ArchiveException):
            ZipConverter().list_contents(BytesIO(b"this is not a zip file"))

    def test_list_contents_corrupt_zip_without_alias_raises_archive_exception(self, monkeypatch):
        # zipfile.BadZipfile is a pre-3.2 alias for BadZipFile. If it is
        # ever removed, "except BadZipfile" fails at except-clause
        # evaluation time. Simulate that by deleting the alias: the fixed
        # code catches the canonical BadZipFile and must still surface
        # ArchiveException, while the old code lets the lookup error escape.
        # Verified: old code raises AttributeError here, new code raises
        # ArchiveException.
        monkeypatch.delattr(zipfile, "BadZipfile", raising=False)
        assert not hasattr(zipfile, "BadZipfile")
        with pytest.raises(ArchiveException):
            ZipConverter().list_contents(BytesIO(b"this is not a zip file"))
