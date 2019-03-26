from os import path
from setuptools import setup


def version():
    init = path.join(path.dirname(__file__), 'ledger', '__init__.py')
    line = list(filter(lambda l: l.startswith('__version__'), open(init)))[0]
    return line.split('=')[-1].strip(" '\"\n")


setup(name='ledger',
      packages=['ledger'],
      version=version(),
      author='Guillermo Guirao Aguilar',
      author_email='contact@guillermoguiraoaguilar.com',
      url='https://github.com/Funk66/ledger',
      classifiers=['Programming Language :: Python :: 3.7'],
      entry_points={
          'console_scripts': [
              'ledger = ledger.gui:main'
          ]
      })
