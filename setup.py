import os
import sys

from setuptools import setup

from __main__ import __version__ as version

with open(os.path.join(os.path.dirname(__file__), 'README.md'), mode='r') as f:
    long_description = f.read()

packages = ['modsmith']

if any('bdist' in arg for arg in sys.argv):
    from nuitka_setuptools import Nuitka, Compile

    build_settings = dict(
        cmdclass={'build_ext': Nuitka},
        ext_modules=Compile(packages)
    )
else:
    build_settings = {}

setup(name='modsmith',
      version=version,
      description='Automatically packages Kingdom Come: Deliverance mods for distribution',
      long_description=long_description,
      author='fireundubh',
      author_email='fireundubh@gmail.com',
      url='https://github.com/fireundubh/modsmith',
      include_package_data=True,
      cmdclass={'build_ext': Nuitka},
      py_modules=['nuitka_setuptools'],
      ext_modules=Compile(['nuitka_setuptools']))
