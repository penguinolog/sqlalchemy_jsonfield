# pylint: disable=missing-docstring, redefined-outer-name

"""Compatibility with alternative JSON libraries (parametrized by the ``codec`` fixture)."""

from __future__ import annotations

import json
import types
import typing

import pytest
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.dialects import mysql
from sqlalchemy.dialects import sqlite

import sqlalchemy_jsonfield
from sqlalchemy_jsonfield.jsonfield import _escape_non_ascii  # pylint: disable=import-private-name
from sqlalchemy_jsonfield.jsonfield import _is_ujson5  # pylint: disable=import-private-name
from sqlalchemy_jsonfield.jsonfield import _join_surrogates  # pylint: disable=import-private-name

if typing.TYPE_CHECKING:
    from conftest import Codec

DATA: dict[str, typing.Any] = {
    "ascii": "value",
    "unicode": "значение",
    "astral": "😀 𝄞",  # Outside of the BMP: surrogate pairs when escaped
    "escapes": 'quote" backslash\\ newline\n tab\t',
    "numbers": [0, -1, 2**40, 1.5],
    "bool": [True, False],
    "null": None,
    "nested": {"list": [], "dict": {}, "ключ": ["элемент"]},
}


def make_field(codec: Codec, enforce_unicode: bool) -> sqlalchemy_jsonfield.JSONField:
    return sqlalchemy_jsonfield.JSONField(
        enforce_string=True,
        enforce_unicode=enforce_unicode,
        json=codec.module,
        **codec.field_kwargs,
    )


def check_encoded(codec: Codec, enforce_unicode: bool, encoded: typing.Any) -> None:
    assert isinstance(encoded, str)
    if enforce_unicode:
        assert "значение" in encoded
        assert "😀" in encoded
    else:
        assert encoded.isascii()
    if codec.strict_json:
        assert json.loads(encoded) == DATA


def test_bind_and_result(codec: Codec, enforce_unicode: bool) -> None:
    field = make_field(codec, enforce_unicode)
    dialect = sqlite.dialect()

    encoded = field.process_bind_param(DATA, dialect)
    check_encoded(codec, enforce_unicode, encoded)
    assert field.process_literal_param(DATA, dialect) == encoded
    assert field.process_result_value(encoded, dialect) == DATA


def test_list_root(codec: Codec, enforce_unicode: bool) -> None:
    field = make_field(codec, enforce_unicode)
    dialect = sqlite.dialect()
    value = ["item", "элемент", 1, None]

    assert field.process_result_value(field.process_bind_param(value, dialect), dialect) == value


def test_reads_stdlib_encoded(codec: Codec, enforce_unicode: bool) -> None:
    """Data already stored by the standard library is readable after the library switch."""
    field = make_field(codec, enforce_unicode)

    assert field.process_result_value(json.dumps(DATA, ensure_ascii=not enforce_unicode), sqlite.dialect()) == DATA


def test_none_passthrough(codec: Codec, enforce_unicode: bool) -> None:
    field = make_field(codec, enforce_unicode)
    dialect = sqlite.dialect()

    assert field.process_bind_param(None, dialect) is None
    assert field.process_result_value(None, dialect) is None


def test_native_json_does_not_use_codec(codec: Codec) -> None:
    """With native JSON type the dialect serializer is used: value is passed through as is."""
    field = sqlalchemy_jsonfield.JSONField(json=codec.module, **codec.field_kwargs)
    dialect = mysql.dialect()

    assert isinstance(field.load_dialect_impl(dialect), sqlalchemy.JSON)
    assert field.process_bind_param(DATA, dialect) is DATA
    assert field.process_result_value(DATA, dialect) is DATA


def test_sqlite_mutable(codec: Codec, enforce_unicode: bool) -> None:
    """End-to-end: store, read, mutate in place and read the raw stored text."""

    class Base(sqlalchemy.orm.DeclarativeBase):
        pass

    class Record(Base):
        __tablename__ = "record"
        id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(primary_key=True)
        data: sqlalchemy.orm.Mapped[dict[str, typing.Any]] = sqlalchemy.orm.mapped_column(
            sqlalchemy_jsonfield.mutable_json_field(
                enforce_string=True,
                enforce_unicode=enforce_unicode,
                json=codec.module,
                **codec.field_kwargs,
            ),
            nullable=False,
        )

    engine = sqlalchemy.create_engine("sqlite://")
    try:
        Base.metadata.create_all(engine)

        with sqlalchemy.orm.Session(engine) as session:
            session.add(Record(id=1, data=dict(DATA)))
            session.commit()

        with sqlalchemy.orm.Session(engine) as session:
            record = session.get_one(Record, 1)
            assert record.data == DATA
            record.data["added"] = "новое"
            session.commit()

        expected = {**DATA, "added": "новое"}
        with sqlalchemy.orm.Session(engine) as session:
            assert session.get_one(Record, 1).data == expected

        with engine.connect() as conn:
            raw = conn.execute(sqlalchemy.text("SELECT data FROM record WHERE id = 1")).scalar_one()
        assert isinstance(raw, str)
        assert raw.isascii() is not enforce_unicode
        assert make_field(codec, enforce_unicode).process_result_value(raw, sqlite.dialect()) == expected
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "value",
    [
        "",
        "ascii only",
        "ж",
        "é߿ࠀ￿",  # 2 and 3 bytes UTF-8 boundaries
        "\U00010000\U0001f600\U0010ffff",  # astral: surrogate pairs
        {"ключ": ["😀", 1, None], "nested": {"é": "\\u0436"}},
    ],
    ids=["empty", "ascii", "cyrillic", "bmp-boundaries", "astral", "structure"],
)
def test_escape_non_ascii_matches_stdlib(value: typing.Any) -> None:
    assert _escape_non_ascii(json.dumps(value, ensure_ascii=False)) == json.dumps(value, ensure_ascii=True)


@pytest.mark.parametrize("factory", [sqlalchemy_jsonfield.JSONField, sqlalchemy_jsonfield.mutable_json_field])
def test_ensure_ascii_in_dumps_kwargs_rejected(factory: typing.Callable[..., typing.Any]) -> None:
    with pytest.raises(ValueError, match="enforce_unicode"):
        factory(enforce_string=True, dumps_kwargs={"ensure_ascii": False})


@pytest.mark.parametrize("result_type", [str, bytes, bytearray, memoryview])
def test_decode_bytes_result_types(result_type: type[typing.Any], enforce_unicode: bool) -> None:
    """Any bytes-like ``dumps`` result is decoded, ``str`` is accepted as is."""

    def dumps(value: typing.Any, **kwargs: typing.Any) -> typing.Any:
        assert not kwargs, "ensure_ascii should not be passed"
        encoded = json.dumps(value, ensure_ascii=False)
        return encoded if result_type is str else result_type(encoded.encode("utf-8"))

    field = sqlalchemy_jsonfield.JSONField(
        enforce_string=True,
        enforce_unicode=enforce_unicode,
        json=types.SimpleNamespace(dumps=dumps, loads=json.loads),
        skip_ensure_ascii=True,
        decode_bytes=True,
    )

    assert field.process_bind_param(DATA, sqlite.dialect()) == json.dumps(DATA, ensure_ascii=not enforce_unicode)


def test_dumps_and_loads_kwargs_forwarded() -> None:
    calls: dict[str, dict[str, typing.Any]] = {}

    def dumps(value: typing.Any, **kwargs: typing.Any) -> str:
        calls["dumps"] = kwargs
        return json.dumps(value)

    def loads(value: str, **kwargs: typing.Any) -> typing.Any:
        calls["loads"] = kwargs
        return json.loads(value)

    field = sqlalchemy_jsonfield.mutable_json_field(
        enforce_string=True,
        json=types.SimpleNamespace(dumps=dumps, loads=loads),
        dumps_kwargs={"sort_keys": True},
        loads_kwargs={"parse_float": float},
    )
    dialect = sqlite.dialect()

    assert field.process_result_value(field.process_bind_param({"key": 1.5}, dialect), dialect) == {"key": 1.5}
    assert calls == {"dumps": {"sort_keys": True, "ensure_ascii": True}, "loads": {"parse_float": float}}


def test_join_surrogates() -> None:
    value = {"\ud83d\ude00": ["\ud83d\ude00 text", "\ud83d", 1, None], "plain": "ж"}

    assert _join_surrogates(value) == {"😀": ["😀 text", "\ud83d", 1, None], "plain": "ж"}


def test_is_ujson5() -> None:
    assert _is_ujson5(types.ModuleType("ujson5"))
    assert _is_ujson5(types.ModuleType("ujson5.core"))
    assert not _is_ujson5(types.ModuleType("ujson"))
    assert not _is_ujson5(json)
    assert not _is_ujson5(types.SimpleNamespace(dumps=json.dumps, loads=json.loads))


def test_ujson5_loads_kwargs_override() -> None:
    """ujson5 defaults are applied under the user arguments."""
    calls: list[dict[str, typing.Any]] = []

    def loads(value: str, **kwargs: typing.Any) -> typing.Any:
        calls.append(kwargs)
        return json.loads(value)

    codec = types.ModuleType("ujson5")
    codec.dumps = json.dumps  # type: ignore[attr-defined]
    codec.loads = loads  # type: ignore[attr-defined]
    dialect = sqlite.dialect()

    sqlalchemy_jsonfield.JSONField(enforce_string=True, json=codec).process_result_value('"\\ud83d\\ude00"', dialect)
    sqlalchemy_jsonfield.JSONField(
        enforce_string=True, json=codec, loads_kwargs={"strict": True, "parse_float": float}
    ).process_result_value("{}", dialect)

    assert calls == [{"strict": False}, {"strict": True, "parse_float": float}]
