#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.md')).read()

with open('requirements/base.txt', 'r') as requirements_file:
    requirements = requirements_file.read().splitlines()

with open('requirements/test.txt', 'r') as requirements_file:
    requirements_test = requirements_file.read().splitlines()

setup(
    name='braspag',
    version='0.5.12',
    description="Python library to consume Braspag SOAP Web services",
    long_description=readme,
    author='Sergio Oliveira',
    author_email='sergio@tracy.com.br',
    url='https://github.com/luizalabs/braspag',
    packages=['braspag'],
    package_data={
        'braspag': ['templates/*.xml'],
    },
    test_suite='tests.suite',
    install_requires=requirements,
    tests_require=requirements_test,
    zip_safe=False,
)
