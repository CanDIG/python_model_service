#!/usr/bin/env python3
"""
Logging wrappers for api calls
"""

import logging
import json
from datetime import datetime
from uuid import UUID
from decorator import decorator
from connexion import request

LOGGERNAME = 'python_model_service'


class FieldEncoder(json.JSONEncoder):
    """Wrap fields to be JSON-safe; handle datetime & UUID"""
    def default(self, obj):   # pylint: disable=E0202
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def structured_log(**kwargs):
    """
    JSON string of keyword arguments
    """
    entrydict = {"timestamp": str(datetime.now())}
    for key in kwargs:
        entrydict[key] = kwargs[key]
    return json.dumps(entrydict, skipkeys=True, cls=FieldEncoder)


def logger():
    """Return the py.logging current logger"""
    return logging.getLogger(LOGGERNAME)


@decorator
def apilog(func, *args, **kwargs):
    """
    Logging decorator for API calls
    """
    entrydict = {"timestamp": str(datetime.now())}
    try:
        entrydict['method'] = request.method
        entrydict['path'] = request.full_path
        entrydict['data'] = str(request.data)
        entrydict['address'] = request.remote_addr
        entrydict['headers'] = str(request.headers)
    except RuntimeError:
        entrydict['called'] = func.__name__
        entrydict['args'] = args
        for key in kwargs:
            entrydict[key] = kwargs[key]

    loc_logger = logging.getLogger('python_model_service')
    logentry = json.dumps(entrydict)
    level = logging.INFO
    loc_logger.log(level, logentry)
    return func(*args, **kwargs)
