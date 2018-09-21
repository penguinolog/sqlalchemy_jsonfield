# coding=utf-8
# pylint: disable=missing-docstring, unused-argument

import unittest

import sqlalchemy.ext.declarative
import sqlalchemy.engine.url
import sqlalchemy.orm
import psycopg2

import sqlalchemy_jsonfield

# Host
# host_name = '127.0.0.1'
host_name = "postgres"

# Login
user = "tester"
password = ""

# Schema name
schema_name = user

# Table name
table_name = "create_test"

# DB Base class
Base = sqlalchemy.ext.declarative.declarative_base()


# Model
class ExampleTable(Base):
    __tablename__ = table_name
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    row_name = sqlalchemy.Column(sqlalchemy.Unicode(64), unique=True)
    json_record = sqlalchemy.Column(sqlalchemy_jsonfield.JSONField(enforce_string=False), nullable=False)


@unittest.skip("Need to update circleci config.")
class PostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.__engine = sqlalchemy.create_engine(
            sqlalchemy.engine.url.URL(
                drivername="postgresql+psycopg2", username=user, password=password, host=host_name, database=schema_name
            ),
            echo=True,
        )

        Base.metadata.create_all(self.__engine)

        # noinspection PyPep8Naming
        Session = sqlalchemy.orm.sessionmaker(self.__engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        ExampleTable.__table__.drop(self.__engine)
        del self.__engine

    def test_operate(self):
        """Check column data operation with unicode specific."""
        test_dict = {"key": "значение"}
        test_list = ["item0", "элемент1"]

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

        with psycopg2.connect(user=user, dbname=schema_name, host=host_name) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT row_name, json_record FROM {tbl}".format(tbl=table_name)
                cursor.execute(sql)
                result = dict(cursor.fetchall())

                self.assertEqual(result["dict_record"], test_dict)

                self.assertEqual(result["list_record"], test_list)
