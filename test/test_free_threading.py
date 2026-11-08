"""Free-threaded (PEP 703) CPython checks."""

from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
import sysconfig
import typing
import unittest

from sqlalchemy.dialects import mysql
from sqlalchemy.dialects import sqlite

import sqlalchemy_jsonfield

if typing.TYPE_CHECKING:
    from conftest import Codec

FREE_THREADED_BUILD = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))


class FreeThreadingTests(unittest.TestCase):
    @unittest.skipUnless(FREE_THREADED_BUILD, "Free-threaded CPython build only")
    def test_gil_not_enabled(self) -> None:
        """Neither the package nor its dependencies re-enable the GIL.

        Checked in a clean interpreter: optional JSON libraries imported by other tests may enable it for this process.
        """
        code = "import sys, sqlalchemy.ext.mutable, sqlalchemy_jsonfield; sys.exit(int(sys._is_gil_enabled()))"
        result = subprocess.run(  # noqa: S603  # trusted input
            [sys.executable, "-W", "error::RuntimeWarning", "-c", code],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, f"GIL was enabled:\n{result.stderr}")

    def test_shared_field_concurrent_use(self) -> None:
        """One field instance is safe to use from many threads at once."""
        field = sqlalchemy_jsonfield.JSONField(enforce_string=True, enforce_unicode=True)
        native = sqlalchemy_jsonfield.JSONField()
        sqlite_dialect = sqlite.dialect()
        mysql_dialect = mysql.dialect()

        def worker(idx: int) -> None:
            for step in range(200):
                value = {"worker": idx, "step": step, "текст": [idx, step]}
                encoded = field.process_bind_param(value, sqlite_dialect)
                self.assertEqual(encoded, json.dumps(value, ensure_ascii=False))
                self.assertEqual(field.process_result_value(encoded, sqlite_dialect), value)
                self.assertIs(native.process_bind_param(value, mysql_dialect), value)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for future in [executor.submit(worker, idx) for idx in range(16)]:
                future.result()


def test_shared_codec_field_concurrent_use(codec: Codec) -> None:
    """One field instance with an alternative JSON library is safe to use from many threads at once."""
    field = sqlalchemy_jsonfield.JSONField(
        enforce_string=True,
        enforce_unicode=False,
        json=codec.module,
        **codec.field_kwargs,
    )
    dialect = sqlite.dialect()

    def worker(idx: int) -> None:
        for step in range(200):
            value = {"worker": idx, "step": step, "текст": [idx, step, "😀"]}
            encoded = field.process_bind_param(value, dialect)
            assert isinstance(encoded, str)
            assert encoded.isascii()
            assert field.process_result_value(encoded, dialect) == value

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for future in [executor.submit(worker, idx) for idx in range(16)]:
            future.result()
