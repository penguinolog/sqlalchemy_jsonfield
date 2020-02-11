#    Copyright 2016 Alexey Stepanov aka penguinolog

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

"""SQLAlchemy JSONField implementation"""

# Standard Library
import ast
import collections
import os.path
import sys

# External Dependencies
import setuptools

try:
    import typing
except ImportError:
    typing = None

PACKAGE_NAME = "sqlalchemy_jsonfield"

with open(os.path.join(os.path.dirname(__file__), PACKAGE_NAME, "__init__.py")) as f:
    SOURCE = f.read()

with open("requirements.txt") as f:
    REQUIRED = f.read().splitlines()

with open("README.rst") as f:
    LONG_DESCRIPTION = f.read()


# noinspection PyUnresolvedReferences
def get_simple_vars_from_src(
    src: str
) -> "typing.Dict[str, typing.Union[str, bytes, int, float, complex, list, set, dict, tuple, None, bool, Ellipsis]]":
    """Get simple (string/number/boolean and None) assigned values from source.

    :param src: Source code
    :type src: str
    :return: OrderedDict with keys, values = variable names, values
    :rtype: typing.Dict[
                str,
                typing.Union[
                    str, bytes,
                    int, float, complex,
                    list, set, dict, tuple,
                    None, bool, Ellipsis
                ]
            ]

    Limitations: Only defined from scratch variables.
    Not supported by design:
        * Imports
        * Executable code, including string formatting and comprehensions.

    Examples:

    >>> string_sample = "a = '1'"
    >>> get_simple_vars_from_src(string_sample)
    OrderedDict([('a', '1')])

    >>> int_sample = "b = 1"
    >>> get_simple_vars_from_src(int_sample)
    OrderedDict([('b', 1)])

    >>> list_sample = "c = [u'1', b'1', 1, 1.0, 1j, None]"
    >>> result = get_simple_vars_from_src(list_sample)
    >>> result == collections.OrderedDict(
    ...     [('c', [u'1', b'1', 1, 1.0, 1j, None])]
    ... )
    True

    >>> iterable_sample = "d = ([1], {1: 1}, {1})"
    >>> get_simple_vars_from_src(iterable_sample)
    OrderedDict([('d', ([1], {1: 1}, {1}))])

    >>> multiple_assign = "e = f = g = 1"
    >>> get_simple_vars_from_src(multiple_assign)
    OrderedDict([('e', 1), ('f', 1), ('g', 1)])
    """
    if sys.version_info[:2] < (3, 8):
        ast_data = (ast.Str, ast.Num, ast.List, ast.Set, ast.Dict, ast.Tuple, ast.Bytes, ast.NameConstant, ast.Ellipsis)
    else:
        ast_data = (ast.Constant, ast.List, ast.Set, ast.Dict, ast.Tuple)

    tree = ast.parse(src)

    result = collections.OrderedDict()

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):  # We parse assigns only
            continue
        try:
            if isinstance(node.value, ast_data):
                value = ast.literal_eval(node.value)
            else:
                continue
        except ValueError:
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and isinstance(tgt.ctx, ast.Store):
                result[tgt.id] = value
    return result


VARIABLES = get_simple_vars_from_src(SOURCE)

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

KEYWORDS = ["sql", "sqlalchemy", "json", "jsonfield", "development"]

setuptools.setup(
    name="SQLAlchemy-JSONField",
    author=VARIABLES["__author__"],
    author_email=VARIABLES["__author_email__"],
    url=VARIABLES["__url__"],
    license=VARIABLES["__license__"],
    description=VARIABLES["__description__"],
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    python_requires=">=3.5.0",
    # While setuptools cannot deal with pre-installed incompatible versions,
    # setting a lower bound is not harmful - it makes error messages cleaner. DO
    # NOT set an upper bound on setuptools, as that will lead to uninstallable
    # situations as progressive releases of projects are done.
    # Blacklist setuptools 34.0.0-34.3.2 due to https://github.com/pypa/setuptools/issues/951
    # Blacklist setuptools 36.2.0 due to https://github.com/pypa/setuptools/issues/1086
    setup_requires=[
        "setuptools >= 21.0.0,!=24.0.0,"
        "!=34.0.0,!=34.0.1,!=34.0.2,!=34.0.3,!=34.1.0,!=34.1.1,!=34.2.0,!=34.3.0,!=34.3.1,!=34.3.2,"
        "!=36.2.0",
        "wheel",
        "setuptools_scm[toml]>=3.4",
    ],
    use_scm_version={"write_to": '{PACKAGE_NAME}/_version.py'.format(PACKAGE_NAME=PACKAGE_NAME)},
    install_requires=REQUIRED,
)
