#!/usr/bin/python3
from setuptools import setup
import io
import os

# Package meta-data
NAME = 'twint'
DESCRIPTION = 'An advanced Twitter scraping & OSINT tool.'
URL = 'https://github.com/twintproject/twint'
EMAIL = 'codyzacharias@pm.me'
AUTHOR = 'Cody Zacharias'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = '2.1.21-fork'

# Packages required
REQUIRED = ['aiohttp', 'aiodns', 'beautifulsoup4', 'dataclasses', 'fake-useragent', 'requests']

here = os.path.abspath(os.path.dirname(__file__))

about = {'__version__': VERSION}

setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description='see original project for description: https://github.com/twintproject/twint',
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=['twint'],
    install_requires=REQUIRED,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
