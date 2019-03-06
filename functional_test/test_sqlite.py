# coding=utf-8
# pylint: disable=missing-docstring, unused-argument

import os.path
import sqlite3
import tempfile
import unittest

import sqlalchemy.ext.declarative
import sqlalchemy.orm

try:
    # noinspection PyPackageRequirements
    import ujson as json
except ImportError:
    import json

import sqlalchemy_jsonfield


# Path to test database
db_path = os.path.join(tempfile.gettempdir(), "test.sqlite3")

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
    def setUp(self):  # type: () -> None
        if os.path.exists(db_path):
            os.remove(db_path)

        engine = sqlalchemy.create_engine("sqlite:///{}".format(db_path), echo=False)

        Base.metadata.create_all(engine)

        # noinspection PyPep8Naming
        Session = sqlalchemy.orm.sessionmaker(engine)
        self.session = Session()

    def test_create(self):  # type: () -> None
        """Check column type"""
        # noinspection PyArgumentList
        with sqlite3.connect(database="file:{}?mode=ro".format(db_path), uri=True) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("PRAGMA TABLE_INFO({})".format(table_name))
            collected = c.fetchall()
            result = [dict(col) for col in collected]

        columns = {info["name"]: info for info in result}

        json_record = columns["json_record"]

        self.assertIn(
            json_record["type"],
            ("TEXT", "JSON"),
            "Unexpected column type: received: {!s}, expected: TEXT|JSON".format(json_record["type"]),
        )

    def test_operate(self):  # type: () -> None
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
            "Dict was changed: {!r} -> {!r}".format(test_dict, dict_record.json_record),
        )

        self.assertEqual(
            list_record.json_record, test_list, "List changed {!r} -> {!r}".format(test_list, list_record.json_record)
        )

        # Low level

        # noinspection PyArgumentList
        with sqlite3.connect(database="file:{}?mode=ro".format(db_path), uri=True) as conn:
            c = conn.cursor()
            c.execute("SELECT row_name, json_record FROM {tbl}".format(tbl=table_name))

            result = dict(c.fetchall())

            self.assertEqual(result["dict_record"], json.dumps(test_dict))

            self.assertEqual(result["list_record"], json.dumps(test_list))
