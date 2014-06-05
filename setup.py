#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.md')).read()


setup(
    name='braspag',
    version='0.4.3',
    description = "Python library to consume Braspag SOAP Web services",
    long_description = readme,
    author='Sergio Oliveira',
    author_email='sergio@tracy.com.br',
    url='https://github.com/TracyWebTech/braspag',
    packages=['braspag'],
    package_data = {
        'braspag': ['templates/*.xml'],
    },
    test_suite='tests.suite',
    install_requires=['Jinja2', 'xmltodict'],
    tests_require=['Mock'],
    zip_safe=False,
)
