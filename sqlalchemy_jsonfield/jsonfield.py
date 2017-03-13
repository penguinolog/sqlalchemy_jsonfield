#    Copyright 2017 Alexey Stepanov aka penguinolog

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""JSONField implementation for SQLAlchemy."""

import sqlalchemy.ext.mutable
import sqlalchemy.types
try:
    # noinspection PyPackageRequirements
    import ujson as json
except ImportError:
    import json

__all__ = ('JSONField', 'mutable_json_field')


# pylint: disable=abstract-method
# noinspection PyAbstractClass
class JSONField(sqlalchemy.types.TypeDecorator):
    """Represent an immutable structure as a json-encoded string or json.

    Usage::

        JSONField(enforce_string=True|False, enforce_unicode=True|False)

    """

    def process_literal_param(self, value, dialect):
        """Re-use of process_bind_param."""
        return self.process_bind_param(value, dialect)

    impl = sqlalchemy.types.TypeEngine  # Special placeholder

    def __init__(
            self,
            enforce_string=False,
            enforce_unicode=False,
            *args,
            **kwargs
    ):
        """JSONField.

        :param enforce_string: enforce String(UnicodeText) type usage
        :type enforce_string: bool
        :param enforce_unicode: do not encode non-ascii data
        :type enforce_unicode: bool
        """
        self.__enforce_string = enforce_string
        self.__enforce_unicode = enforce_unicode
        super(JSONField, self).__init__(*args, **kwargs)

    def __use_json(self, dialect):
        """Helper to determine, which encoder to use."""
        return (
            hasattr(dialect, '_json_serializer') and not self.__enforce_string
        )

    def load_dialect_impl(self, dialect):
        """Select impl by dialect."""
        if self.__use_json(dialect):
            return dialect.type_descriptor(sqlalchemy.JSON)
        return dialect.type_descriptor(sqlalchemy.UnicodeText)

    def process_bind_param(self, value, dialect):
        """Encode data, if required."""
        if self.__use_json(dialect) or value is None:
            return value

        # pylint: disable=no-member
        return json.dumps(
            value,
            ensure_ascii=not self.__enforce_unicode
        )
        # pylint: enable=no-member

    def process_result_value(self, value, dialect):
        """Decode data, if required."""
        if self.__use_json(dialect) or value is None:
            return value

        # pylint: disable=no-member
        return json.loads(value)
        # pylint: enable=no-member
# pylint: enable=abstract-method


def mutable_json_field(
    enforce_string=False,
    enforce_unicode=False,
    *args,
    **kwargs
):
    """Mutable JSONField creator.

    :param enforce_string: enforce String(UnicodeText) type usage
    :type enforce_string: bool
    :param enforce_unicode: do not encode non-ascii data
    :type enforce_unicode: bool
    :return: Mutable JSONField via MutableDict.as_mutable
    :rtype: JSONField
    """
    return sqlalchemy.ext.mutable.MutableDict.as_mutable(
        JSONField(
            enforce_string=enforce_string,
            enforce_unicode=enforce_unicode,
            *args,
            **kwargs
        )
    )
