"""Shared fixtures: JSON libraries supported as ``JSONField(json=...)``."""

from __future__ import annotations

import dataclasses
import typing

import pytest

if typing.TYPE_CHECKING:
    import types
    from collections.abc import Callable


@dataclasses.dataclass(frozen=True)
class CodecCase:
    """JSON library with the field arguments required to use it."""

    module_name: str
    # Extra JSONField / mutable_json_field keyword arguments, built from the imported module.
    field_kwargs: Callable[[types.ModuleType], dict[str, typing.Any]] = lambda _module: {}
    # Output is a strict JSON (not JSON5 extensions), readable by the standard library.
    strict_json: bool = True


CODEC_CASES: dict[str, CodecCase] = {
    "json": CodecCase("json"),
    "simplejson": CodecCase("simplejson"),
    "ujson": CodecCase("ujson"),
    "rapidjson": CodecCase("rapidjson"),
    "ujson5": CodecCase("ujson5"),
    "ujson5-json5-syntax": CodecCase(
        "ujson5",
        # Not key_quotation="none": ujson5 writes non-identifier keys ("null", "1", "a b") unquoted, unreadable
        field_kwargs=lambda _module: {"dumps_kwargs": {"key_quotation": "single", "trailing_comma": True}},
        strict_json=False,
    ),
    "orjson": CodecCase("orjson", field_kwargs=lambda _module: {"skip_ensure_ascii": True, "decode_bytes": True}),
    "orjson-options": CodecCase(
        "orjson",
        field_kwargs=lambda module: {
            "skip_ensure_ascii": True,
            "decode_bytes": True,
            "dumps_kwargs": {"option": module.OPT_SORT_KEYS | module.OPT_APPEND_NEWLINE},
        },
    ),
}


@dataclasses.dataclass(frozen=True)
class Codec:
    """Imported JSON library ready for the field construction."""

    name: str
    module: types.ModuleType
    field_kwargs: dict[str, typing.Any]
    strict_json: bool


@pytest.fixture(params=list(CODEC_CASES), ids=list(CODEC_CASES))
def codec(request: pytest.FixtureRequest) -> Codec:
    """JSON library under test: skipped if not installed (no wheels for the interpreter)."""
    case = CODEC_CASES[request.param]
    module = pytest.importorskip(case.module_name)
    return Codec(
        name=request.param,
        module=module,
        field_kwargs=case.field_kwargs(module),
        strict_json=case.strict_json,
    )


@pytest.fixture(params=[False, True], ids=["ascii", "unicode"])
def enforce_unicode(request: pytest.FixtureRequest) -> bool:
    """Both encoding modes: escaped non-ASCII and raw UTF-8."""
    return typing.cast("bool", request.param)
