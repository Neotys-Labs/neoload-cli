from setuptools import setup, find_packages

setup(
    name='neoload-cli',
    version='1.0.0',
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
    ]
)
