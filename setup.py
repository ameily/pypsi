
from setuptools import setup

setup(
    name='pypsi',
    version='1.0-rc1',
    license='BSD',
    description='Python Pluggable Shell Interface',
    long_description='Pluggable framework for developing command line interfaces',
    author='Adam Meily',
    author_email='meily.adam@gmail.com',
    url='https://github.com/ameily/pypsi',
    packages=['pypsi', 'pypsi.commands', 'pypsi.plugins'],
    platforms=[],
    install_requires=[
        'chardet==2.0.1'
    ],
    keywords=[
        'cli', 'command line', 'command line interface', 'shell', 'terminal',
        'console', 'term', 'command prompt', 
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Terminals'
    ]
)

