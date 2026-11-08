SQLAlchemy-JSONField
====================

.. image:: https://github.com/penguinolog/sqlalchemy_jsonfield/workflows/Python%20package/badge.svg
    :target: https://github.com/penguinolog/sqlalchemy_jsonfield/actions
.. image:: https://img.shields.io/pypi/v/sqlalchemy_jsonfield.svg
    :target: https://pypi.python.org/pypi/sqlalchemy_jsonfield
.. image:: https://img.shields.io/pypi/pyversions/sqlalchemy_jsonfield.svg
    :target: https://pypi.python.org/pypi/sqlalchemy_jsonfield
.. image:: https://img.shields.io/pypi/status/sqlalchemy_jsonfield.svg
    :target: https://pypi.python.org/pypi/sqlalchemy_jsonfield
.. image:: https://img.shields.io/github/license/penguinolog/sqlalchemy_jsonfield.svg
    :target: https://raw.githubusercontent.com/penguinolog/sqlalchemy_jsonfield/master/LICENSE
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff

SQLALchemy JSONField implementation for storing dicts at SQL independently from JSON type support.

Why?
----

SqlAlchemy provides JSON field support for several database types (PostgreSQL and MySQL for now)
and semi-working dict <-> JSON <-> VARCHAR example, but...
In real scenarios we have tests on sqlite, production on MySQL/MariaDB/Percona/PostgreSQL
and some of them (modern Oracle MySQL & PostgreSQL) support JSON,
some of them (SQLite, Percona & MariaDB) requires data conversion to Text (not VARCHAR).

As addition, we have different levels of Unicode support on database and connector side,
so we may be interested to switch JSON encoding between deployments.

.. note:: SQLite 3.9 supports JSON natively and SQLAlchemy can handle this.

Solution:
---------

SQLALchemy JSONField has API with suport for automatic switch between native JSON and JSON encoded data,
and encoding to JSON string can be enforced.

Pros:
-----

* Free software: Apache license
* Open Source: https://github.com/penguinolog/sqlalchemy_jsonfield
* Self-documented code: docstrings with types in comments
* Uses native JSON by default, but allows to specify different library.
* Support multiple Python versions

Usage
=====
Direct usage with MariaDB (example extracted from functional tests):

.. code-block:: python

  import sqlalchemy_jsonfield

  class ExampleTable(Base):
      __tablename__ = table_name
      id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
      row_name = sqlalchemy.Column(
          sqlalchemy.Unicode(64),
          unique=True,
      )
      json_record = sqlalchemy.Column(
          sqlalchemy_jsonfield.JSONField(
              # MariaDB does not support JSON for now
              enforce_string=True,
              # MariaDB connector requires additional parameters for correct UTF-8
              enforce_unicode=False
          ),
          nullable=False
      )

Usage with alternate JSON library:

.. code-block:: python

  import sqlalchemy_jsonfield
  import ujson

  class ExampleTable(Base):
      __tablename__ = table_name
      id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
      row_name = sqlalchemy.Column(
          sqlalchemy.Unicode(64),
          unique=True,
      )
      json_record = sqlalchemy.Column(
          sqlalchemy_jsonfield.JSONField(
              enforce_string=True,
              enforce_unicode=False,
              json=ujson,  # Use ujson instead of standard json.
          ),
          nullable=False
      )

Usage on PostgreSQL/Oracle MySQL(modern version)/SQLite(testing) environments allows to set `enforce_string=False`
and use native JSON fields.

Alternative JSON libraries
--------------------------

Any object with ``dumps`` and ``loads`` callables can be passed as ``json``.
The library is used only for the text storage: ``enforce_string=True`` or a dialect without native JSON support.
With native JSON the dialect serializer is used, configure it on the engine instead:

.. code-block:: python

  engine = sqlalchemy.create_engine(
      url,
      json_serializer=lambda value: orjson.dumps(value).decode(),
      json_deserializer=orjson.loads,
  )

Extra keyword-only arguments (``JSONField`` and ``mutable_json_field``) adapt libraries with a different API:

* ``dumps_kwargs``: extra keyword arguments for ``dumps`` (``ensure_ascii`` is not allowed: use ``enforce_unicode``).
* ``loads_kwargs``: extra keyword arguments for ``loads``.
* ``skip_ensure_ascii``: do not pass ``ensure_ascii`` to ``dumps``. The library should produce UTF-8 output;
  without ``enforce_unicode`` non-ASCII characters are escaped after encoding, the same way as the standard ``json`` does.
* ``decode_bytes``: ``dumps`` returns ``bytes``: decode it as UTF-8.

Supported libraries (covered by the compatibility tests on every supported interpreter where the library installs):

==================== ============== ============================================= =================================================
Package (PyPI)       ``json=``      Required additional arguments                 Notes
==================== ============== ============================================= =================================================
standard library     ``json``       none (default)
``simplejson``       ``simplejson`` none
``ujson``            ``ujson``      none
``python-rapidjson`` ``rapidjson``  none                                          re-enables the GIL on free-threaded builds
``ujson5``           ``ujson5``     none                                          detected automatically, decoder workarounds below
``orjson``           ``orjson``     ``skip_ensure_ascii=True, decode_bytes=True`` CPython with GIL only (no other wheels)
==================== ============== ============================================= =================================================

Compatible, but not in the test matrix:

* ``pysimdjson`` (``json=simdjson``): no additional arguments; it speeds up only ``loads``, ``dumps`` is the standard one.

Not supported:

* ``yyjson``: the decoder corrupts non-ASCII strings (UTF-8 is read as Latin-1, upstream PR #17 is not released),
  ``dumps`` can not encode a root-level string and does not accept writer flags.
* ``msgspec``: ``msgspec.json`` has no ``dumps``/``loads`` (``encode``/``decode`` API instead).

orjson, options are passed via ``dumps_kwargs``:

.. code-block:: python

  import orjson

  sqlalchemy_jsonfield.JSONField(
      enforce_string=True,
      json=orjson,
      skip_ensure_ascii=True,  # orjson.dumps has no ensure_ascii: escaping is done by JSONField if required
      decode_bytes=True,  # orjson.dumps returns bytes
      dumps_kwargs={"option": orjson.OPT_SORT_KEYS},
  )

ujson5 (JSON5) is detected automatically and ujson5 decoder flaws are handled:

* ``loads`` is called with ``strict=False`` by default: in the strict mode ujson5 rejects valid escaped
  ``\n``, ``\t``, ``\r`` and ``\0`` in strings. Explicit ``loads_kwargs`` take priority.
* Escaped UTF-16 surrogate pairs (characters outside the BMP, like emoji, escaped without ``enforce_unicode``)
  are joined after decoding: ujson5 returns them as separate lone surrogates.

JSON5 output options are passed via ``dumps_kwargs``. Data encoded with JSON5 extensions is readable only by JSON5
parsers, so do not mix it with native JSON columns or other libraries:

.. code-block:: python

  import ujson5

  sqlalchemy_jsonfield.JSONField(
      enforce_string=True,
      json=ujson5,
      dumps_kwargs={"key_quotation": "single", "trailing_comma": True},
  )

.. warning:: Do not use ``key_quotation="none"`` with ujson5: keys which are not identifiers
             (``"null"``, ``"true"``, ``"1"``, ``"a b"``) are written unquoted and can not be read back.

Testing
=======
The main test mechanism for the package `sqlalchemy_jsonfield` is using `tox`.
Available environments can be collected via `tox -l`

Compatibility tests with alternative JSON libraries are parametrized over all libraries listed above
(``codecs`` and ``codecs-gil`` dependency groups); libraries which are not installed are skipped.

CI systems
==========
For code checking several CI systems is used in parallel:

1. `GitHub actions: <https://github.com/penguinolog/sqlalchemy_jsonfield/actions>`_ is used for checking: PEP8, pylint, bandit, installation possibility and unit tests.
