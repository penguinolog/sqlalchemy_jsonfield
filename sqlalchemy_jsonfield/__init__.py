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

"""Implement JSONField for SQLAlchemy."""

# External Dependencies
import pkg_resources

# Local Implementation
from .jsonfield import JSONField
from .jsonfield import mutable_json_field

try:  # pragma: no cover
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:  # pragma: no cover
    # package is not installed, try to get from SCM
    try:
        # noinspection PyPackageRequirements,PyUnresolvedReferences
        import setuptools_scm  # type: ignore

        __version__ = setuptools_scm.get_version()
    except ImportError:
        pass


__all__ = ("JSONField", "mutable_json_field")

__author__ = "Alexey Stepanov <penguinolog@gmail.com>"
__author_email__ = "penguinolog@gmail.com"
__url__ = "https://github.com/penguinolog/sqlalchemy_jsonfield"
__description__ = "SQLALchemy JSONField implementation for storing dicts at SQL"
__license__ = "Apache License, Version 2.0"
