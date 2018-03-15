# coding=utf-8

from cx_Freeze import Executable, setup

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    'packages': ['lxml.etree', 'lxml._elementpath'],
    'optimize': 2,
    'include_msvcr': False,
    'zip_include_packages': '*',
    'zip_exclude_packages': ''
}

setup(name='Modsmith',
      version='0.1.2',
      description='Automatically packages Kingdom Come: Deliverance mods for distribution',
      options={'build_exe': build_exe_options},
      executables=[Executable('__main__.py', base=None, targetName='modsmith.exe')])
