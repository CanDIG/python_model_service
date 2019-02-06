#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for `python_model_service` package."""

import subprocess


def test_dredd():
    subprocess.check_call(['dredd', '--hookfiles=dreddhooks.py'],
                          cwd='./tests')
