FROM python:latest
RUN pip install -U setuptools tox pip
ADD . /mnt/test
WORKDIR /mnt/test
RUN rm -f **/*.pyc && rm -rf **/__pycache__

CMD tox -e functional
