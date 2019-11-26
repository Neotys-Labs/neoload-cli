from setuptools import find_packages, setup

from os import path
from io import open
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='neoload',
      version='0.3.2',
      description='A command-line native utility for launching and observing NeoLoad performance tests',
      url='https://github.com/Neotys-Labs/neoload-cli',
      author='Paul Bruce',
      author_email='me@paulsbruce.io',
      license='Apache 2.0',
      packages=find_packages(exclude=("tests",)),
      python_requires='>3.5.2',
      classifiers=[
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3.7'
      ],
      install_requires=[
          'click',
          'six',
          'wcwidth','pygments','prompt_toolkit==1.0.14', # fix for PyInquirer (below) and python3
          'PyInquirer',
          'pyfiglet',
          'termcolor',
          'pprint',
          'docker',
          'coloredlogs',
      ],
      entry_points={
        'console_scripts': [
            'neoload=neoload.__main__:main'
        ]
      },
      zip_safe=False,
      long_description_content_type='text/markdown',
      long_description=long_description
)
