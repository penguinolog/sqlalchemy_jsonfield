SQLALchemy_JSONField
====================

.. image:: https://travis-ci.org/penguinolog/sqlalchemy_jsonfield.svg?branch=master
    :target: https://travis-ci.org/penguinolog/sqlalchemy_jsonfield
.. image:: https://coveralls.io/repos/github/penguinolog/sqlalchemy_jsonfield/badge.svg?branch=master
    :target: https://coveralls.io/github/penguinolog/sqlalchemy_jsonfield?branch=master
.. image:: https://img.shields.io/github/license/penguinolog/sqlalchemy_jsonfield.svg
    :target: https://raw.githubusercontent.com/penguinolog/sqlalchemy_jsonfield/master/LICENSE

SQLALchemy JSONField implementation for storing dicts at SQL independently from JSON type support.

Pros:

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
