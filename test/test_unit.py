# coding=utf-8
# pylint: disable=missing-docstring, unused-argument

from __future__ import absolute_import
from __future__ import unicode_literals

import unittest

try:
    import ujson as json
except ImportError:
    import json

import sqlalchemy.types
from sqlalchemy.dialects import mysql, sqlite

import sqlalchemy_jsonfield


# noinspection PyStatementEffect
class BaseFunctionality(unittest.TestCase):
    def test_impl(self):
        # impl placeholder
        self.assertIsInstance(
            sqlalchemy_jsonfield.JSONField().impl,
            sqlalchemy.types.TypeEngine
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.mutable_json_field().impl,
            sqlalchemy.types.TypeEngine
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.JSONField().load_dialect_impl(
                mysql.dialect()
            ),
            sqlalchemy.types.JSON
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.mutable_json_field().load_dialect_impl(
                mysql.dialect()
            ),
            sqlalchemy.types.JSON
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.JSONField().load_dialect_impl(
                sqlite.dialect()
            ),
            sqlalchemy.types.UnicodeText
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.mutable_json_field().load_dialect_impl(
                sqlite.dialect()
            ),
            sqlalchemy.types.UnicodeText
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.JSONField(
                enforce_string=True
            ).load_dialect_impl(
                mysql.dialect()
            ),
            sqlalchemy.types.UnicodeText
        )

        self.assertIsInstance(
            sqlalchemy_jsonfield.mutable_json_field(
                enforce_string=True
            ).load_dialect_impl(
                mysql.dialect()
            ),
            sqlalchemy.types.UnicodeText
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField().process_bind_param(
                {'key': 'val'},
                mysql.dialect()
            ),
            {'key': 'val'}
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField().process_literal_param(
                {'key': 'val'},
                mysql.dialect()
            ),
            {'key': 'val'}
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField(
                enforce_string=True
            ).process_bind_param(
                {'key': 'val'},
                mysql.dialect()
            ),
            json.dumps({'key': 'val'})
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField(
                enforce_string=True
            ).process_bind_param(
                {'key': 'val'},
                sqlite.dialect()
            ),
            json.dumps({'key': 'val'})
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField(
                enforce_string=True,
                enforce_unicode=True
            ).process_bind_param(
                {'ключ': 'значение'},
                sqlite.dialect()
            ),
            json.dumps({'ключ': 'значение'}, ensure_ascii=False)
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField().process_result_value(
                json.dumps({'key': 'val'}),
                mysql.dialect()),
            json.dumps({'key': 'val'})
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField(
                enforce_string=True,
            ).process_result_value(
                json.dumps({'key': 'val'}),
                mysql.dialect()),
            {'key': 'val'}
        )

        self.assertEqual(
            sqlalchemy_jsonfield.JSONField().process_result_value(
                json.dumps({'key': 'val'}),
                sqlite.dialect()),
            {'key': 'val'}
        )
