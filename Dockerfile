FROM python:slim
# Build tools. Mandatory for the future tests support
RUN apt-get update && apt-get upgrade -y && apt-get install -y libpq-dev gcc
# Test runner and actual packaging tools
RUN pip install -U setuptools tox pip
# Copy tests
ADD . /mnt/test
WORKDIR /mnt/test
# Pre-cleanup for local run
RUN rm -f **/*.pyc && rm -rf **/__pycache__

# Default target: run functional tests, which requires FS access.
CMD tox -e functional
