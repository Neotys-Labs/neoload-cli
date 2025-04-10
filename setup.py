from setuptools import setup, find_packages

from os import path
from io import open

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='neoload',
    include_package_data=True,
    packages=find_packages(exclude=("tests",)),
    entry_points={
        'console_scripts': [
            'neoload=neoload.__main__:cli'
        ]
    },
    setup_requires=['setuptools_scm==8.2.0'],
    use_scm_version={
        'write_to': 'neoload/version.py',
        'write_to_template': '__version__ = "{version}"',
        'tag_regex': r'^(?P<prefix>v)?(?P<version>[^\+]+)(?P<suffix>.*)?$'
    },
    url='https://github.com/Neotys-Labs/neoload-cli',
    license='Apache 2.0',
    author='Neotys',
    author_email='',
    description='A command-line native utility for launching and observing NeoLoad performance tests',
    install_requires=[
        'click>=7',
        'pyconfig',
        'appdirs',
        'requests>=2.25.1',
        'jsonschema',
        'PyYAML>=5',
        'junit_xml',
        'termcolor',
        'coloredlogs',
        'gitignorefile',
        'jinja2',
        'python-dateutil', # for 3.6 compatibility
        'tqdm',
        'requests_toolbelt',
        'urllib3>=1.26.5',
        'docker',
        'pyparsing',
        'simplejson',
        'colorama',
        'importlib-resources'
    ],
    tests_require=[
        "pytest",
        "pytest-datafiles",
    ],
    long_description_content_type='text/markdown',
    long_description=long_description
)
