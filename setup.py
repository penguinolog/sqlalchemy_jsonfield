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

import setuptools

import sqlalchemy_jsonfield

with open('README.rst') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.readlines()

setuptools.setup(
    name='SQLAlchemy_JSONField',
    version=sqlalchemy_jsonfield.__version__,
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='sql sqlalchemy json jsonfield development',
    url='https://github.com/penguinolog/sqlalchemy_jsonfield',
    license='Apache License, Version 2.0',
    author='Alexey Stepanov',
    author_email='penguinolog@gmail.com',
    description='SQLALchemy JSONField implementation for storing dicts at SQL',
    long_description=long_description,
    requires=required,
    extras_require={
        ':platform_python_implementation == "CPython"': [
            'ujson',
        ],
    },
)
