#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `python_model_service` package."""

import pytest
import subprocess

def test_dredd():
    ret_val = subprocess.run(['dredd', '--hookfiles=dreddhooks.py'],
                             cwd='./tests', check=True)
