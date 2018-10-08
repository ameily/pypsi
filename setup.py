#
# Copyright (c) 2015, Adam Meily <meily.adam@gmail.com>
# Pypsi - https://github.com/ameily/pypsi
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

# import platform
import os
import sys
from setuptools import setup
import pypsi


def load_requirements(filename):
    path = os.path.join(os.path.dirname(__file__), 'requirements', filename)
    return [line for line in open(path, 'r').readlines() if line.strip() and not line.startswith('#')]


requirements = load_requirements('requirements.txt')
if sys.version_info[:2] == (3, 3):
    dev_requirements = load_requirements('requirements-dev-py33.txt')
else:
    dev_requirements = load_requirements('requirements-dev.txt')


print(requirements)

setup(
    name='pypsi',
    version=pypsi.__version__,
    license='ISC',
    description='Python Pluggable Shell Interface',
    long_description=open("README.rst", 'r').read(),
    author='Adam Meily',
    author_email='meily.adam@gmail.com',
    url='https://github.com/ameily/pypsi',
    download_url='https://pypi.python.org/pypi/pypsi',
    packages=['pypsi', 'pypsi.commands', 'pypsi.plugins', 'pypsi.os'],
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements
    },
    keywords=[
        'cli', 'command line', 'command line interface', 'shell', 'terminal',
        'console', 'term', 'command prompt',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Terminals'
    ]
)
