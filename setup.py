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

from setuptools import setup
import platform
import pypsi


def read(path):
    return open(path, 'r').read()


install_requires = ['chardet>=2.0.1']
if platform.system() == 'Windows':
    install_requires.append('pyreadline-ais>=2.0.3')


setup(
    name='pypsi',
    version=pypsi.__release__,
    license='ISC',
    description='Python Pluggable Shell Interface',
    long_description=read("README.rst"),
    author='Adam Meily',
    author_email='meily.adam@gmail.com',
    url='https://github.com/ameily/pypsi',
    download_url='https://pypi.python.org/pypi/pypsi',
    packages=['pypsi', 'pypsi.commands', 'pypsi.plugins', 'pypsi.os'],
    install_requires=install_requires,
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
