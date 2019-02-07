# Python Model Service

Based on a CanDIG [OpenAPI variant service demo](https://github.com/ljdursi/openapi_calls_example), this toy service demonstrates the Python OpenAPI stack with CanDIG API best practices.

[![Build Status](https://travis-ci.org/CanDIG/python_model_service.svg?branch=master)](https://travis-ci.org/CanDIG/python_model_service)
[![CodeFactor](https://www.codefactor.io/repository/github/CanDIG/python_model_service/badge)](https://www.codefactor.io/repository/github/CanDIG/python_model_service)
[![PyUp](https://pyup.io/repos/github/CanDIG/python_model_service/shield.svg)](https://pyup.io/repos/github/CanDIG/python_model_service/)
[![Quay.io](https://quay.io/repository/candig/python_model_service/status)](https://quay.io/repository/candig/python_model_service)

## Stack

- [Connexion](https://github.com/zalando/connexion) for implementing the API
- [SQLAlchemy](http://sqlalchemy.org), using [Sqlite3](https://www.sqlite.org/index.html) for ORM
- [Bravado-core](https://github.com/Yelp/bravado-core) for Python classes from the spec
- [Dredd](https://dredd.readthedocs.io/en/latest/) and [Dredd-Hooks-Python](https://github.com/apiaryio/dredd-hooks-python) for testing
- Python 3
- Pytest, tox
- Travis-CI

## Installation

The server software can be installed in a virtual environment:

```
pip install -r requirements.txt
pip install -r requirements_dev.txt
python setup.py develop
```

for automated testing you can install dredd; assuming you already have node and npm installed,

```
npm install -g dredd
```

### Running

The server can be run with, for instance

```
python3 -m python_model_service --database=test.db --logfile=test.log --loglevel=WARN
```

For testing, the dredd config is currently set up to launch the service itself, so no server needs be running:

```
cd tests
dredd --hookfiles=dreddhooks.py
```
