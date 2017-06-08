CHANGELOG
=========
Version 0.6.5
-------------
* Use `ast.literal_eval` instead of `eval` in isolated env for `__init__.py` parsing.
* Do not rely on `six` in `setup.py`.

Version 0.6.4
-------------
* Fix readme naming.

Version 0.6.3
-------------
* Remove name duplication (setup.py|setup.cfg)

Version 0.6.2
-------------
* Move the most metadata from `setup.py` to `setup.cfg`.
* Move `requirements.txt` to `setup.cfg`.
* Replace `_` by `-` in name.

Version 0.6.0
-------------
* Allow to run setup.py on not installed package (`__init__.py` imports fix).

Version 0.5.0
-------------
* Development Status :: 4 - Beta (functional tests passed multiple times in several db configurations)

* Update docs

* Example in README

* Fixed docstrings (now covered by pep257 checker)

Version 0.3.2
-------------
Technical bump: Start of CI/CD usage

Version 0.3.1
-------------
Technical bump: fix case in human-readable package name

Version 0.3.0
-------------
* Added mutable generator as way to reduce amount of imports in model

Version 0.2.0
-------------
* Do not use mutable wrapper due to lack of arguments: lets use in table models

Version 0.1.0
-------------
* Initial release: Minimally tested (SQLite in memory, manual)
