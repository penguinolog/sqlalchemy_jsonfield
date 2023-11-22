# pylint: disable=missing-docstring, unused-argument

from __future__ import annotations

import unittest

import pymysql.cursors
import sqlalchemy.engine.url
import sqlalchemy.ext.declarative
import sqlalchemy.orm

try:
    import ujson as json
except ImportError:
    import json

import sqlalchemy_jsonfield

# Host
# host_name = '127.0.0.1'
host_name = "mariadb"

# Login
user = "root"
password = ""

# Schema name
schema_name = "test_schema"

# Table name
table_name = "create_test"

# DB Base class
Base = sqlalchemy.ext.declarative.declarative_base()


# Model
class ExampleTable(Base):
    __tablename__ = table_name
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)  # noqa: A003
    row_name = sqlalchemy.Column(sqlalchemy.Unicode(64), unique=True)
    json_record = sqlalchemy.Column(
        sqlalchemy_jsonfield.JSONField(enforce_string=True), nullable=False  # MariaDB does not support JSON for now
    )


@unittest.skip("Need to update circleci config.")
class MySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with pymysql.connect(host=host_name, user=user, password=password, charset="utf8") as cursor:
            # Read a single record
            sql = f"DROP SCHEMA IF EXISTS {schema_name};CREATE SCHEMA {schema_name};"
            cursor.execute(sql)

    @classmethod
    def tearDownClass(cls):
        with pymysql.connect(host=host_name, user=user, password=password, charset="utf8") as cursor:
            # Read a single record
            sql = f"DROP SCHEMA IF EXISTS {schema_name};"
            cursor.execute(sql)

    def setUp(self):
        engine = sqlalchemy.create_engine(
            sqlalchemy.engine.url.URL(
                drivername="mysql+pymysql", username=user, password=password, host=host_name, database=schema_name
            ),
            echo=False,
        )

        Base.metadata.create_all(engine)

        # noinspection PyPep8Naming
        Session = sqlalchemy.orm.sessionmaker(engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def test_operate(self):
        """Check column data operation with unicode specific."""
        test_dict = {"key": "значение"}
        test_list = ["item0", "элемент1"]  # noqa: RUF001

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
            list_record.json_record, test_list, f"List changed {test_list!r} -> {list_record.json_record!r}"
        )

        with pymysql.connect(host=host_name, user=user, password=password, db=schema_name, charset="utf8") as cursor:
            # Read a single record
            sql = f"SELECT row_name, json_record FROM {table_name}"  # noqa: S608
            cursor.execute(sql)
            result = dict(cursor.fetchall())

            self.assertEqual(result["dict_record"], json.dumps(test_dict))

            self.assertEqual(result["list_record"], json.dumps(test_list))
