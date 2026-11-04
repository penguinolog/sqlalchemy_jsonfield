# pylint: disable=missing-docstring, unused-argument

from __future__ import annotations

import contextlib
import json
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest

import sqlalchemy.orm

try:
    from sqlalchemy.orm import declarative_base  # sqlalchemy 2
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base


import sqlalchemy_jsonfield

# Table name
table_name = "create_test"

# DB Base class
Base = declarative_base()


# Model
class ExampleTable(Base):
    __tablename__ = table_name
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    row_name = sqlalchemy.Column(sqlalchemy.Unicode(64), unique=True)
    json_record = sqlalchemy.Column(sqlalchemy_jsonfield.JSONField(), nullable=False)


class SQLIteTests(unittest.TestCase):
    def setUp(self) -> None:
        # Separate temporary directory per test: parallel runs and leftovers from aborted runs do not collide.
        self.db_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"sqlalchemy_jsonfield_{sys.implementation.name}_"))
        self.db_path = self.db_dir / "test.sqlite3"

        self.engine = sqlalchemy.create_engine(f"sqlite:///{self.db_path}", echo=False)

        Base.metadata.create_all(self.engine)

        # noinspection PyPep8Naming
        self.session: sqlalchemy.orm.Session = sqlalchemy.orm.Session(self.engine, future=True)

    def tearDown(self) -> None:
        with contextlib.suppress(Exception):
            # We are closing session, if close failed - it will be done on process exit
            self.session.close()

        # Release pooled connections: Windows can not remove a file which is still open.
        self.engine.dispose()

        # On CI we do not always have permissions to do it.
        shutil.rmtree(self.db_dir, ignore_errors=True)

    def test_create(self) -> None:
        """Check column type."""
        # noinspection PyArgumentList
        with contextlib.closing(sqlite3.connect(database=f"file:{self.db_path}?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(f"PRAGMA TABLE_INFO({table_name})")
            collected = c.fetchall()
            result = [dict(col) for col in collected]

        columns = {info["name"]: info for info in result}

        json_record = columns["json_record"]

        self.assertIn(
            json_record["type"],
            ("TEXT", "JSON"),
            "Unexpected column type: received: {!s}, expected: TEXT|JSON".format(json_record["type"]),
        )

    def test_operate(self) -> None:
        """Check column data operation."""
        test_dict = {"key": "value"}
        test_list = ["item0", "item1"]

        # fill table

        with self.session:
            self.session.add_all(
                [
                    ExampleTable(row_name="dict_record", json_record=test_dict),
                    ExampleTable(row_name="list_record", json_record=test_list),
                ]
            )
            self.session.commit()

        # Validate backward check

        dict_record = self.session.query(ExampleTable).filter(ExampleTable.row_name == "dict_record").one()

        list_record = self.session.query(ExampleTable).filter(ExampleTable.row_name == "list_record").one()

        self.assertEqual(
            dict_record.json_record,
            test_dict,
            f"Dict was changed: {test_dict!r} -> {dict_record.json_record!r}",
        )

        self.assertEqual(
            list_record.json_record,
            test_list,
            f"List changed {test_list!r} -> {list_record.json_record!r}",
        )

        # Low level

        # noinspection PyArgumentList
        with contextlib.closing(sqlite3.connect(database=f"file:{self.db_path}?mode=ro", uri=True)) as conn:
            c = conn.cursor()
            c.execute(f"SELECT row_name, json_record FROM {table_name}")  # noqa: S608

            result = dict(c.fetchall())

            self.assertEqual(result["dict_record"], json.dumps(test_dict))

            self.assertEqual(result["list_record"], json.dumps(test_list))

    def test_literal_render(self) -> None:
        """Check literal rendered values are stored as data."""
        test_dict = {"key": "it's (SELECT 1)"}
        test_str = "(SELECT 'injected')"

        with self.session:
            for row_name, value in (("dict_literal", test_dict), ("str_literal", test_str)):
                self.session.execute(
                    sqlalchemy.insert(ExampleTable).values(
                        row_name=row_name,
                        json_record=sqlalchemy.bindparam(
                            row_name,
                            value,
                            type_=ExampleTable.__table__.c.json_record.type,
                            literal_execute=True,
                        ),
                    )
                )
            self.session.commit()

        dict_record = self.session.query(ExampleTable).filter(ExampleTable.row_name == "dict_literal").first()

        str_record = self.session.query(ExampleTable).filter(ExampleTable.row_name == "str_literal").first()

        self.assertEqual(dict_record.json_record, test_dict)

        self.assertEqual(str_record.json_record, test_str)
