from setuptools import setup

setup(name='neoload',
      version='0.2',
      description='A command-line native utility for launching and observing NeoLoad performance tests',
      url='https://github.com/paulsbruce/neoload-cli',
      author='Paul Bruce',
      author_email='me@paulsbruce.io',
      license='Apache 2.0',
      packages=['neoload'],
      python_requires='>3.5.2',
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
      zip_safe=False)
