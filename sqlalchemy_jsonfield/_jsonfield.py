"""JSONField implementation for SQLAlchemy"""

import sqlalchemy.ext.mutable
import sqlalchemy.types
try:
    import ujson as json
except ImportError:
    import json


class _JSONField(sqlalchemy.types.TypeDecorator):
    """Represents an immutable structure as a json-encoded string or json

    Usage::

        JSONField(enforce_string=True|False, enforce_unicode=True|False)

    """

    def process_literal_param(self, value, dialect):
        """Re-use of process_bind_param"""
        return self.process_bind_param(value, dialect)

    @property
    def python_type(self):
        """Expect dict as JSON"""
        return dict

    impl = sqlalchemy.types.TypeEngine  # Special placeholder

    def __init__(
            self,
            enforce_string=False,
            enforce_unicode=False,
            *args,
            **kwargs
    ):
        """JSONField

        :param enforce_string: enforce String(UnicodeText) type usage
        :param enforce_unicode: do not encode non-ascii data
        """
        self.__enforce_string = enforce_string
        self.__enforce_unicode = enforce_unicode
        super(_JSONField, self).__init__(*args, **kwargs)

    def __use_json(self, dialect):
        """Helper to determine, which encoder to use"""
        return (
            hasattr(dialect, '_json_serializer') and not self.__enforce_string
        )

    def load_dialect_impl(self, dialect):
        """Select impl by dialect"""
        if self.__use_json(dialect):
            return dialect.type_descriptor(sqlalchemy.JSON)
        return dialect.type_descriptor(sqlalchemy.UnicodeText)

    def process_bind_param(self, value, dialect):
        """Encode data, if required"""
        if self.__use_json(dialect) or value is None:
            return value

        # pylint: disable=no-member
        return json.dumps(
            value,
            ensure_ascii=not self.__enforce_unicode
        )
        # pylint: enable=no-member

    def process_result_value(self, value, dialect):
        """Decode data, if required"""
        if self.__use_json(dialect) or value is None:
            return value

        # pylint: disable=no-member
        return json.loads(value)
        # pylint: enable=no-member


JSONField = sqlalchemy.ext.mutable.MutableDict.as_mutable(_JSONField)

__all__ = ['JSONField']
