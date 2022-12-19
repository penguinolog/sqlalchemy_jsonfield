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
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

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

Testing
=======
The main test mechanism for the package `sqlalchemy_jsonfield` is using `tox`.
Available environments can be collected via `tox -l`

CI systems
==========
For code checking several CI systems is used in parallel:

1. `GitHub actions: <https://github.com/penguinolog/sqlalchemy_jsonfield/actions>`_ is used for checking: PEP8, pylint, bandit, installation possibility and unit tests.
