# pylint: disable=missing-docstring, unused-argument

from __future__ import annotations

# Standard Library
import datetime
import os.path
import sqlite3
import tempfile
import unittest

# External Dependencies
import sqlalchemy.ext.declarative
import sqlalchemy.orm

try:
    # External Dependencies
    import ujson as json
except ImportError:
    import json

# Package Implementation
import sqlalchemy_jsonfield

# Table name
table_name = "create_test"

# DB Base class
Base = sqlalchemy.ext.declarative.declarative_base()


# Model
class ExampleTable(Base):
    __tablename__ = table_name
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    row_name = sqlalchemy.Column(sqlalchemy.Unicode(64), unique=True)
    json_record = sqlalchemy.Column(sqlalchemy_jsonfield.JSONField(), nullable=False)


class SQLIteTests(unittest.TestCase):
    def setUp(self) -> None:
        # Path to test database
        time_component = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        self.db_path = os.path.join(tempfile.gettempdir(), f"test.sqlite3_{time_component}")

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        engine = sqlalchemy.create_engine(f"sqlite:///{self.db_path}", echo=False)

        Base.metadata.create_all(engine)

        # noinspection PyPep8Naming
        Session = sqlalchemy.orm.sessionmaker(engine)
        self.session = Session()

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create(self) -> None:
        """Check column type"""
        # noinspection PyArgumentList
        with sqlite3.connect(database=f"file:{self.db_path}?mode=ro", uri=True) as conn:
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
        """Check column data operation"""
        test_dict = {"key": "value"}
        test_list = ["item0", "item1"]

        # fill table

        with self.session.transaction:
            self.session.add_all(
                [
                    ExampleTable(row_name="dict_record", json_record=test_dict),
                    ExampleTable(row_name="list_record", json_record=test_list),
                ]
            )

        # Validate backward check

        dict_record = self.session.query(ExampleTable).filter(ExampleTable.row_name == "dict_record").first()

        list_record = self.session.query(ExampleTable).filter(ExampleTable.row_name == "list_record").first()

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
        with sqlite3.connect(database=f"file:{self.db_path}?mode=ro", uri=True) as conn:
            c = conn.cursor()
            c.execute(f"SELECT row_name, json_record FROM {table_name}")

            result = dict(c.fetchall())

            self.assertEqual(result["dict_record"], json.dumps(test_dict))

            self.assertEqual(result["list_record"], json.dumps(test_list))
