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

# Standard Library
import json
import typing

# External Dependencies
import sqlalchemy.ext.mutable
import sqlalchemy.types

if typing.TYPE_CHECKING:
    import types  # noqa: F401  # pylint: disable=unused-import
    from sqlalchemy.engine.default import DefaultDialect  # noqa: F401  # pylint: disable=unused-import
    from sqlalchemy.sql.type_api import TypeEngine  # noqa: F401  # pylint: disable=unused-import

__all__ = ("JSONField", "mutable_json_field")


# noinspection PyAbstractClass
class JSONField(sqlalchemy.types.TypeDecorator):  # pylint: disable=abstract-method
    """Represent an immutable structure as a json-encoded string or json.

    Usage::

        JSONField(enforce_string=True|False, enforce_unicode=True|False)

    """

    def process_literal_param(self, value, dialect):  # type: (typing.Any, DefaultDialect) -> typing.Any
        """Re-use of process_bind_param."""
        return self.process_bind_param(value, dialect)

    impl = sqlalchemy.types.TypeEngine  # Special placeholder

    def __init__(  # pylint: disable=keyword-arg-before-vararg
        self,
        enforce_string=False,  # type: bool
        enforce_unicode=False,  # type: bool
        json=json,  # type: typing.Union[types.ModuleType, typing.Any]
        json_type=sqlalchemy.JSON,  # type: TypeEngine
        *args,  # type: typing.Any
        **kwargs  # type: typing.Any
    ):  # type: (...) -> None
        """JSONField.

        :param enforce_string: enforce String(UnicodeText) type usage
        :type enforce_string: bool
        :param enforce_unicode: do not encode non-ascii data
        :type enforce_unicode: bool
        :param json: JSON encoding/decoding library. By default: standard json package.
        :param json_type: the sqlalchemy/dialect class that will be used to render the DB JSON type.
                          By default: sqlalchemy.JSON
        """
        self.__enforce_string = enforce_string
        self.__enforce_unicode = enforce_unicode
        self.__json_codec = json
        self.__json_type = json_type
        super(JSONField, self).__init__(*args, **kwargs)

    def __use_json(self, dialect):  # type: (DefaultDialect) -> bool
        """Helper to determine, which encoder to use."""
        return hasattr(dialect, "_json_serializer") and not self.__enforce_string

    def load_dialect_impl(self, dialect):  # type: (DefaultDialect) -> TypeEngine
        """Select impl by dialect."""
        if self.__use_json(dialect):
            return dialect.type_descriptor(self.__json_type)
        return dialect.type_descriptor(sqlalchemy.UnicodeText)

    def process_bind_param(self, value, dialect):  # type: (typing.Any, DefaultDialect) -> typing.Union[str, typing.Any]
        """Encode data, if required."""
        if self.__use_json(dialect) or value is None:
            return value

        return self.__json_codec.dumps(value, ensure_ascii=not self.__enforce_unicode)  # pylint: disable=no-member

    def process_result_value(
        self,
        value,  # type: typing.Union[str, typing.Any]
        dialect  # type: DefaultDialect
    ):  # type: (...) -> typing.Any
        """Decode data, if required."""
        if self.__use_json(dialect) or value is None:
            return value

        return self.__json_codec.loads(value)  # pylint: disable=no-member


def mutable_json_field(  # pylint: disable=keyword-arg-before-vararg
    enforce_string=False,  # type: bool
    enforce_unicode=False,  # type: bool
    json=json,  # type: typing.Union[types.ModuleType, typing.Any]
    *args,  # type: typing.Any
    **kwargs  # type: typing.Any
):  # type: (...) -> JSONField
    """Mutable JSONField creator.

    :param enforce_string: enforce String(UnicodeText) type usage
    :type enforce_string: bool
    :param enforce_unicode: do not encode non-ascii data
    :type enforce_unicode: bool
    :param json: JSON encoding/decoding library.
                 By default: standard json package.
    :return: Mutable JSONField via MutableDict.as_mutable
    :rtype: JSONField
    """
    return sqlalchemy.ext.mutable.MutableDict.as_mutable(
        JSONField(enforce_string=enforce_string, enforce_unicode=enforce_unicode, json=json, *args, **kwargs)
    )
