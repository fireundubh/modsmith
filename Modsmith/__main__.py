import argparse
import os
import shutil
import sys
from ctypes import windll
from distutils.version import StrictVersion
from platform import release, version

import colorama

from Modsmith import __version__
from Modsmith.Packager import Packager
from Modsmith.ProjectOptions import ProjectOptions
from Modsmith.ProjectSettings import ProjectSettings
from Modsmith.SimpleLogger import SimpleLogger as Log


class Application:
    def __init__(self, args: argparse.Namespace) -> None:
        self.options: ProjectOptions = ProjectOptions(args)
        self.settings: ProjectSettings = ProjectSettings(self.options)
        self.debug: bool = self.options.debug

    @staticmethod
    def _try_enable_ansi_colors() -> None:
        colorama.init()

        # VT support must be enabled manually for post-AU windows 10 platforms
        # see: https://github.com/Microsoft/WSL/issues/1173#issuecomment-254250445
        if sys.platform == 'win32' and release() == '10':
            if StrictVersion(version()) >= StrictVersion('10.0.14393'):
                kernel32 = windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    def _try_reset_build_path(self) -> None:
        if os.path.exists(self.settings.project_build_path):
            shutil.rmtree(self.settings.project_build_path, ignore_errors=True)
            os.makedirs(self.settings.project_build_path, exist_ok=True)

    def run(self) -> int:
        self._try_enable_ansi_colors()

        config_path = self.options.config_path
        project_manifest_path = self.settings.project_manifest_path
        project_build_path = self.settings.project_build_path
        project_data_path = self.settings.project_data_path
        project_i18n_path = self.settings.project_i18n_path

        make_project_relative = self.settings.make_project_relative

        if not config_path:
            Log.error('Cannot proceed because "kingdomcome.yaml" was not found')
            return 1

        packager: Packager = Packager(self.settings)

        if not os.path.exists(project_manifest_path):
            Log.error('Cannot proceed because "mod.manifest" was not found in project root')
            return 1

        self._try_reset_build_path()

        # create pak, if project has game data
        if os.path.exists(project_data_path):
            Log.info('Started building package...',
                     prefix=os.linesep)

            packager.generate_pak()

            Log.info('PAK generation completed.',
                     prefix=os.linesep)
        else:
            Log.warn('Cannot find Data in project root. Skipping PAK generation.',
                     prefix=os.linesep)

        # create localization paks, if project has localization
        if os.path.exists(project_i18n_path):
            Log.info('Started building localization...',
                     prefix=os.linesep)

            packager.generate_i18n()

            Log.info('i18n generation completed.',
                     prefix=os.linesep)
        else:
            Log.warn('Cannot find Localization in project root. Skipping PAK generation.',
                     prefix=os.linesep)

        # create build
        if os.path.exists(project_build_path):
            Log.info('Started building ZIP archive...',
                     prefix=os.linesep)

            output_path: str = packager.pack()

            Log.info('ZIP generation completed. File path: "%s"' % make_project_relative(output_path),
                     prefix=os.linesep)
        else:
            Log.error('Cannot generate ZIP because the Build folder was not found')
            return 1

        return 0


if __name__ == '__main__':
    _parser = argparse.ArgumentParser(description='Modsmith v%s by fireundubh' % __version__)

    _parser.add_argument('manifest_path',
                         metavar='MANIFEST_PATH', nargs=1,
                         action='store', type=str,
                         help='Path to mod.manifest in project root')

    _group1 = _parser.add_argument_group('path arguments')

    _group1.add_argument('--config-path',
                         action='store', type=str, default='',
                         help='Path to YAML configuration')

    _group2 = _parser.add_argument_group('miscellaneous arguments')

    _group2.add_argument('--pack-assets',
                         action='store_true', default=False,
                         help='Pack all assets')

    _group2.add_argument('--debug',
                         action='store_true', default=False,
                         help='Enable logging tracebacks')

    Application(_parser.parse_args()).run()
