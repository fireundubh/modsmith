import argparse
import os
import platform
import shutil
import sys

from ctypes import windll

import colorama

from modsmith import (ProjectOptions,
                      ProjectSettings,
                      to_version,
                      SimpleLogger as Log,
                      Packager)


class Application:
    def __init__(self, args: argparse.Namespace) -> None:
        self.options = ProjectOptions(args)
        self.settings = ProjectSettings(self.options)
        self.debug: bool = self.options.debug

    @staticmethod
    def _try_enable_ansi_colors() -> None:
        colorama.init()

        # VT support must be enabled manually for post-AU windows 10 platforms
        # see: https://github.com/Microsoft/WSL/issues/1173#issuecomment-254250445
        if os.environ.get('MODSMITH_DEBUG', False):
            return

        if sys.platform == 'win32' and platform.release() == '10':
            if to_version(platform.version()) >= to_version('10.0.14393'):
                kernel32 = windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    def _try_reset_build_path(self) -> None:
        if os.path.exists(self.settings.project_build_path):
            shutil.rmtree(self.settings.project_build_path, ignore_errors=True)
            os.makedirs(self.settings.project_build_path, exist_ok=True)

    def run(self) -> int:
        self._try_enable_ansi_colors()

        make_project_relative = self.settings.make_project_relative

        if not self.options.config_path:
            Log.error('Cannot proceed because "kingdomcome.yaml" was not found')
            return 1

        packager: Packager = Packager(self.settings)

        if not os.path.exists(self.settings.project_manifest_path):
            Log.error('Cannot proceed because "mod.manifest" was not found in project root')
            return 1

        self._try_reset_build_path()

        # create pak, if project has game data
        if os.path.exists(self.settings.project_data_path):
            Log.info('Started building package...',
                     prefix=os.linesep)

            packager.generate_pak()

            Log.info('PAK generation completed.',
                     prefix=os.linesep)
        else:
            Log.warn('Cannot find Data in project root. Skipping PAK generation.',
                     prefix=os.linesep)

        # create localization paks, if project has localization
        if os.path.exists(self.settings.project_i18n_path):
            Log.info('Started building localization...',
                     prefix=os.linesep)

            packager.generate_i18n()

            Log.info('i18n generation completed.',
                     prefix=os.linesep)
        else:
            Log.warn('Cannot find Localization in project root. Skipping PAK generation.',
                     prefix=os.linesep)

        # create build
        if os.path.exists(self.settings.project_build_path):
            Log.info('Started building ZIP archive...',
                     prefix=os.linesep)

            output_path: str = packager.pack()

            Log.info('ZIP generation completed. File path: "%s"' % make_project_relative(output_path),
                     prefix=os.linesep)
        else:
            Log.error('Cannot generate ZIP because the Build folder was not found')
            return 1

        return 0
