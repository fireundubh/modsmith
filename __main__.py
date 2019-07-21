# coding=utf-8

import argparse
import os
import shutil

from Modsmith.Packager import Packager
from Modsmith.ProjectOptions import ProjectOptions
from Modsmith.ProjectSettings import ProjectSettings
from Modsmith.SimpleLogger import SimpleLogger as Log

__version__ = '0.2.0'


class Application:
    def __init__(self, args: argparse.Namespace) -> None:
        self.options: ProjectOptions = ProjectOptions(args)
        self.settings: ProjectSettings = ProjectSettings(self.options)
        self.debug: bool = self.options.debug

    def run(self) -> None:
        if not self.options.config_path:
            raise FileNotFoundError('Cannot find kingdomcome.yaml')

        packager = Packager(self.settings)

        if not os.path.exists(self.settings.project_manifest_path):
            raise FileNotFoundError('[ERR] Cannot find required mod.manifest in project root')

        if os.path.exists(self.settings.project_build_path):
            shutil.rmtree(self.settings.project_build_path, ignore_errors=True)
            os.makedirs(self.settings.project_build_path, exist_ok=True)

        # create pak, if project has game data
        if os.path.exists(self.settings.project_data_path):
            Log.info('Starting PAK generation...', os.linesep)
            packager.generate_pak()
            Log.info('PAK generation complete.', os.linesep)
        else:
            Log.warn('Cannot find Data in project root. Skipping PAK generation.', os.linesep)

        # create localization paks, if project has localization
        if os.path.exists(self.settings.project_localization_path):
            Log.info('Starting i18n generation...', os.linesep)
            packager.generate_i18n()
            Log.info('i18n generation complete.', os.linesep)
        else:
            Log.warn('Cannot find Localization in project root. Skipping PAK generation.', os.linesep)

        # create redistributable
        if os.path.exists(self.settings.project_build_path):
            Log.info('Starting ZIP generation...', os.linesep)
            output_path: str = packager.pack()
            Log.info('ZIP generation complete. File path: {}'.format(output_path), os.linesep)
        else:
            raise NotADirectoryError('[ERR] Cannot package mod because Build directory was not found\n\t'
                                     'Possible reasons:\n\t\t'
                                     '1. Project has no Data.\n\t\t'
                                     '2. Project has no Localization.')


if __name__ == '__main__':
    _parser = argparse.ArgumentParser(description='Modsmith v%s by fireundubh' % __version__)

    _group1 = _parser.add_argument_group('path arguments')

    _group1.add_argument('-c', '--config-path',
                         action='store', type=str, default=os.path.join(os.path.dirname(__file__), 'kingdomcome.yaml'),
                         help='Path to YAML configuration')

    _group1.add_argument('-i', '--project-path',
                         required=True,
                         action='store', type=str, default='',
                         help='Path to project')

    _group1.add_argument('-l', '--localization-path',
                         action='store', type=str, default='',
                         help='Path to localization')

    _group2 = _parser.add_argument_group('file arguments')

    _group2.add_argument('-o', '--pak-file-name',
                         action='store', type=str, default='',
                         help='Target PAK file name')

    _group2.add_argument('-z', '--zip-file-name',
                         action='store', type=str, default='',
                         help='Target ZIP file name')

    _group3 = _parser.add_argument_group('miscellaneous arguments')

    _group3.add_argument('--pack-assets',
                         action='store_true', default=False,
                         help='Pack all assets')

    _group3.add_argument('--debug',
                         action='store_true', default=False,
                         help='Enable logging tracebacks')

    Application(_parser.parse_args()).run()
