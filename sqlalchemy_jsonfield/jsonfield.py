#    Copyright 2017-2026 Alexey Stepanov aka penguinolog

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at

#         http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""JSONField implementation for SQLAlchemy."""

from __future__ import annotations

import json
import re
import typing

import sqlalchemy.ext.mutable
import sqlalchemy.types

if typing.TYPE_CHECKING:
    import types
    from collections.abc import Mapping

    from sqlalchemy.engine import Dialect
    from sqlalchemy.sql.type_api import TypeEngine

__all__ = ("JSONField", "mutable_json_field")

_NON_ASCII = re.compile(r"[^\x00-\x7f]")


def _escape_non_ascii_char(match: re.Match[str]) -> str:
    r"""Escape a single non-ASCII character as JSON ``\uXXXX`` sequence (surrogate pair outside of the BMP).

    :param match: regex match of exactly one non-ASCII character
    :type match: re.Match[str]
    :return: escape sequence, identical to the standard ``json`` module output
    :rtype: str
    """
    if (code := ord(match.group())) < 0x10000:
        return f"\\u{code:04x}"
    code -= 0x10000
    return f"\\u{0xD800 | (code >> 10):04x}\\u{0xDC00 | (code & 0x3FF):04x}"


def _escape_non_ascii(encoded: str) -> str:
    """Make encoded JSON ASCII-only.

    In valid JSON non-ASCII characters can appear only inside string literals,
    where an escape sequence is equivalent to the character itself.

    :param encoded: encoded JSON document
    :type encoded: str
    :return: the same document with all non-ASCII characters escaped
    :rtype: str
    """
    if encoded.isascii():
        return encoded
    return _NON_ASCII.sub(_escape_non_ascii_char, encoded)


_SURROGATE = re.compile(r"[\ud800-\udfff]")


def _join_surrogates(value: typing.Any) -> typing.Any:
    """Join UTF-16 surrogate pairs left by a decoder into the real characters in all decoded strings.

    Unpaired surrogates are kept as is.

    :param value: decoded JSON value
    :type value: typing.Any
    :return: the same structure with fixed strings
    :rtype: typing.Any
    """
    if isinstance(value, str):
        if _SURROGATE.search(value) is None:
            return value
        return value.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "surrogatepass")
    if isinstance(value, dict):
        return {_join_surrogates(key): _join_surrogates(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_join_surrogates(item) for item in value]
    return value


def _is_ujson5(codec: typing.Any) -> bool:
    """Check whether JSON library is ujson5 (or its submodule) and requires decoder workarounds.

    :param codec: JSON library
    :type codec: typing.Any
    :return: codec is ujson5
    :rtype: bool
    """
    name = getattr(codec, "__name__", "")
    return isinstance(name, str) and name.partition(".")[0] == "ujson5"


# noinspection PyAbstractClass
class JSONField(sqlalchemy.types.TypeDecorator):  # type: ignore[type-arg]  # pylint: disable=too-many-instance-attributes
    r"""Represent an immutable structure as a json-encoded string or json.

    Usage::

        JSONField(enforce_string=True | False, enforce_unicode=True | False)

    JSON library is any object with ``dumps`` and ``loads`` callables (module, class, namespace).
    Libraries with a non-standard ``dumps`` signature are supported via extra arguments, for example ``orjson``::

        JSONField(enforce_string=True, json=orjson, skip_ensure_ascii=True, decode_bytes=True)

    ``ujson5`` is detected automatically and its decoder flaws are worked around:
    ``strict=False`` is used by default (escaped ``\n``, ``\t`` are rejected in the strict mode)
    and escaped surrogate pairs (characters outside the BMP, like emoji) are joined after decoding.
    """

    def process_literal_param(self, value: typing.Any, dialect: Dialect) -> typing.Any:
        """Re-use of process_bind_param.

        :return: encoded value if required
        :rtype: typing.Union[str, typing.Any]
        """
        return self.process_bind_param(value, dialect)

    impl = sqlalchemy.types.TypeEngine  # Special placeholder
    cache_ok = False  # Cache complexity due to requirement of value re-serialization and mutability

    def __init__(  # pylint: disable=keyword-arg-before-vararg
        self,
        enforce_string: bool = False,
        enforce_unicode: bool = False,
        json: types.ModuleType | typing.Any = json,  # pylint: disable=redefined-outer-name
        json_type: TypeEngine[typing.Any] | type[TypeEngine[typing.Any]] = sqlalchemy.JSON,
        *args: typing.Any,
        skip_ensure_ascii: bool = False,
        decode_bytes: bool = False,
        dumps_kwargs: Mapping[str, typing.Any] | None = None,
        loads_kwargs: Mapping[str, typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> None:
        """JSONField.

        :param enforce_string: enforce String(UnicodeText) type usage
        :type enforce_string: bool
        :param enforce_unicode: do not encode non-ascii data
        :type enforce_unicode: bool
        :param json: JSON encoding/decoding library. By default: standard json package.
        :param json_type: the sqlalchemy/dialect class that will be used to render the DB JSON type.
                          By default: sqlalchemy.JSON
        :param args: extra baseclass arguments
        :type args: typing.Any
        :param skip_ensure_ascii: do not pass ``ensure_ascii`` to ``dumps`` (library does not support it, like orjson).
                                  Library is expected to produce UTF-8 output; if ``enforce_unicode`` is not set,
                                  non-ASCII characters are escaped after encoding.
        :type skip_ensure_ascii: bool
        :param decode_bytes: ``dumps`` returns ``bytes`` (like orjson): decode result as UTF-8.
        :type decode_bytes: bool
        :param dumps_kwargs: extra keyword arguments for ``dumps`` (like ujson5 ``key_quotation`` or orjson ``option``).
                             ``ensure_ascii`` is not allowed: it is controlled by ``enforce_unicode``.
        :type dumps_kwargs: typing.Mapping[str, typing.Any] | None
        :param loads_kwargs: extra keyword arguments for ``loads``. ujson5: ``{"strict": False}`` is used by default.
        :type loads_kwargs: typing.Mapping[str, typing.Any] | None
        :param kwargs: extra baseclass keyworded arguments
        :type kwargs: typing.Any
        :raises ValueError: ``ensure_ascii`` is passed in ``dumps_kwargs``
        """
        dumps_kwargs = dict(dumps_kwargs or {})
        if "ensure_ascii" in dumps_kwargs:
            raise ValueError("ensure_ascii is controlled by enforce_unicode, do not pass it in dumps_kwargs")
        if not skip_ensure_ascii:
            dumps_kwargs["ensure_ascii"] = not enforce_unicode

        self.__escape_non_ascii = skip_ensure_ascii and not enforce_unicode
        self.__decode_bytes = decode_bytes
        self.__dumps_kwargs = dumps_kwargs
        self.__join_surrogates = _is_ujson5(json)
        if self.__join_surrogates:
            # ujson5 strict mode rejects valid escaped control characters (\n, \t, \r, \0) in strings
            self.__loads_kwargs: dict[str, typing.Any] = {"strict": False, **(loads_kwargs or {})}
        else:
            self.__loads_kwargs = dict(loads_kwargs or {})
        self.__enforce_string = enforce_string
        self.__json_codec = json
        self.__json_type = json_type
        super().__init__(*args, **kwargs)

    def __use_json(self, dialect: Dialect) -> bool:
        """Determine which encoder to use.

        :return: use engine-based json encoder
        :rtype: bool
        """
        return hasattr(dialect, "_json_serializer") and not self.__enforce_string

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[typing.Any]:
        """Select impl by dialect.

        :return: dialect implementation depends on decoding method
        :rtype: TypeEngine
        """
        # types are handled by DefaultDialect, Dialect class is abstract
        if self.__use_json(dialect):
            return dialect.type_descriptor(self.__json_type)  # type: ignore[arg-type]
        return dialect.type_descriptor(sqlalchemy.UnicodeText)  # type: ignore[arg-type]

    def process_bind_param(self, value: typing.Any, dialect: Dialect) -> str | typing.Any:
        """Encode data, if required.

        :return: encoded value if required
        :rtype: typing.Union[str, typing.Any]
        """
        if self.__use_json(dialect) or value is None:
            return value

        encoded = self.__json_codec.dumps(value, **self.__dumps_kwargs)
        if self.__decode_bytes and isinstance(encoded, (bytes, bytearray, memoryview)):
            encoded = bytes(encoded).decode("utf-8")
        if self.__escape_non_ascii:
            return _escape_non_ascii(encoded)
        return encoded

    def process_result_value(self, value: str | typing.Any, dialect: Dialect) -> typing.Any:
        """Decode data, if required.

        :return: decoded result value if required
        :rtype: typing.Any
        """
        if self.__use_json(dialect) or value is None:
            return value

        decoded = self.__json_codec.loads(value, **self.__loads_kwargs)
        if self.__join_surrogates:
            return _join_surrogates(decoded)
        return decoded


def mutable_json_field(  # pylint: disable=keyword-arg-before-vararg, redefined-outer-name
    enforce_string: bool = False,
    enforce_unicode: bool = False,
    json: types.ModuleType | typing.Any = json,
    *args: typing.Any,
    skip_ensure_ascii: bool = False,
    decode_bytes: bool = False,
    dumps_kwargs: Mapping[str, typing.Any] | None = None,
    loads_kwargs: Mapping[str, typing.Any] | None = None,
    **kwargs: typing.Any,
) -> JSONField:
    """Mutable JSONField creator.

    :param enforce_string: enforce String(UnicodeText) type usage
    :type enforce_string: bool
    :param enforce_unicode: do not encode non-ascii data
    :type enforce_unicode: bool
    :param json: JSON encoding/decoding library.
                 By default: standard json package.
    :param args: extra baseclass arguments
    :type args: typing.Any
    :param skip_ensure_ascii: do not pass ``ensure_ascii`` to ``dumps`` (library does not support it, like orjson).
    :type skip_ensure_ascii: bool
    :param decode_bytes: ``dumps`` returns ``bytes`` (like orjson): decode result as UTF-8.
    :type decode_bytes: bool
    :param dumps_kwargs: extra keyword arguments for ``dumps``.
    :type dumps_kwargs: typing.Mapping[str, typing.Any] | None
    :param loads_kwargs: extra keyword arguments for ``loads``. ujson5: ``{"strict": False}`` is used by default.
    :type loads_kwargs: typing.Mapping[str, typing.Any] | None
    :param kwargs: extra baseclass keyworded arguments
    :type kwargs: typing.Any
    :return: Mutable JSONField via MutableDict.as_mutable
    :rtype: JSONField
    """
    return sqlalchemy.ext.mutable.MutableDict.as_mutable(  # type: ignore[return-value]
        JSONField(  # type: ignore[misc]
            enforce_string=enforce_string,
            enforce_unicode=enforce_unicode,
            json=json,
            *args,  # noqa: B026
            skip_ensure_ascii=skip_ensure_ascii,
            decode_bytes=decode_bytes,
            dumps_kwargs=dumps_kwargs,
            loads_kwargs=loads_kwargs,
            **kwargs,
        )
    )
