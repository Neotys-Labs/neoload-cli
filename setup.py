from setuptools import setup, find_packages

from os import path
from io import open

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='neoload-cli',
    version='1.0.0.rc1',
    package_data={'': [
        'LICENSE',
        'README.md'
    ]},
    packages=find_packages(exclude=("tests",)),
    entry_points={
        'console_scripts': [
            'neoload=neoload.__main__:cli'
        ]
    },
    url='https://github.com/Neotys-Labs/neoload-cli',
    license='Apache 2.0',
    author='Neotys',
    author_email='',
    description='A command-line native utility for launching and observing NeoLoad performance tests',
    install_requires=[
        'click',
        'pyconfig',
        'appdirs',
        'requests',
        'jsonschema',
        'PyYAML',
        'pytest',
        'pytest-datafiles',
        'junit_xml',
        'termcolor',
        'coloredlogs'
    ],
    long_description_content_type='text/markdown',
    long_description=long_description
)
