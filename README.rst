SQLAlchemy-JSONField
====================

.. image:: https://travis-ci.org/penguinolog/sqlalchemy_jsonfield.svg?branch=master
    :target: https://travis-ci.org/penguinolog/sqlalchemy_jsonfield
.. image:: https://coveralls.io/repos/github/penguinolog/sqlalchemy_jsonfield/badge.svg?branch=master
    :target: https://coveralls.io/github/penguinolog/sqlalchemy_jsonfield?branch=master
.. image:: https://img.shields.io/circleci/project/github/penguinolog/sqlalchemy_jsonfield.svg
    :target: https://circleci.com/gh/penguinolog/sqlalchemy_jsonfield
.. image:: https://img.shields.io/pypi/v/sqlalchemy_jsonfield.svg
    :target: https://pypi.python.org/pypi/sqlalchemy_jsonfield
.. image:: https://img.shields.io/pypi/pyversions/sqlalchemy_jsonfield.svg
    :target: https://pypi.python.org/pypi/sqlalchemy_jsonfield
.. image:: https://img.shields.io/pypi/status/sqlalchemy_jsonfield.svg
    :target: https://pypi.python.org/pypi/sqlalchemy_jsonfield
.. image:: https://img.shields.io/github/license/penguinolog/sqlalchemy_jsonfield.svg
    :target: https://raw.githubusercontent.com/penguinolog/sqlalchemy_jsonfield/master/LICENSE

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

Solution:
---------

SQLALchemy JSONField has API with suport for automatic switch between native JSON and JSON encoded data,
and encoding to JSON string can be enforced.

Pros:
-----

* Free software: Apache license
* Open Source: https://github.com/penguinolog/sqlalchemy_jsonfield
* Self-documented code: docstrings with types in comments
* Uses native JSON, if possible
* Support miltiple Python versions:

::

    Python 2.7
    Python 3.4
    Python 3.5
    Python 3.6
    PyPy
    PyPy3

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


Usage on PostgreSQL/Oracle MySQL(modern version)/SQLite(testing) environments allows to set `enforce_string=False`
and use native JSON fields.

Testing
=======
The main test mechanism for the package `sqlalchemy_jsonfield` is using `tox`.
Test environments available:

::

    pep8
    py27
    py34
    py35
    py36
    pypy
    pypy3
    pylint
    docs

CI systems
==========
For code checking several CI systems is used in parallel:

1. `Travis CI: <https://travis-ci.org/penguinolog/sqlalchemy_jsonfield>`_ is used for checking: PEP8, pylint, bandit, installation possibility and unit tests. Also it's publishes coverage on coveralls.

2. `coveralls: <https://coveralls.io/github/penguinolog/sqlalchemy_jsonfield>`_ is used for coverage display.

3. `Circle CI: <https://circleci.com/gh/penguinolog/sqlalchemy_jsonfield>`_ is used for functional tests at separate docker infrastructure. This CI used for **HUGE** tests.

CD system
=========
`Travis CI: <https://travis-ci.org/penguinolog/sqlalchemy_jsonfield>`_ is used for package delivery on PyPI.
