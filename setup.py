
from distutils.core import setup

setup(
    name='pypsi',
    version='0.1',
    license='BSD',
    description='Python Pluggable Shell Interface',
    long_description='Pluggable framework for developing command line interfaces',
    author='Adam Meily',
    author_email='meily.adam@gmail.com',
    url='https://github.com/ameily/pypsi',
    packages=['pypsi', 'pypsi.commands', 'pypsi.plugins'],
    platforms=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
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

