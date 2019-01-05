# coding=utf-8

import argparse
import os
import traceback

from modules.Packager import Packager
from modules.SimpleLogger import SimpleLogger as Log


class ArgFileNotFoundError(FileNotFoundError):
    pass


class ArgNotADirectoryError(NotADirectoryError):
    pass


class ArgValueError(ValueError):
    pass


def print_exception(exception):
    if args.debug:
        print('%s%s' % (os.linesep, traceback.format_exc()))
    else:
        print('%s%s: %s%s' % (os.linesep, type(exception).__name__, exception, os.linesep))


def main():
    try:
        if not os.path.exists('modsmith.conf'):
            if not args.cfg or args.cfg and not os.path.exists(args.cfg):
                raise ArgFileNotFoundError('[ERR] Cannot find modsmith.conf\n\t'
                                           'Possible reasons:\n\t\t'
                                           '1. The modsmith.conf file does not exist in the Modsmith install path.\n\t\t'
                                           '2. The working directory was not set to the Modsmith install path.')

        if not args.project:
            raise ArgValueError('[ERR] Cannot pass None for project_path')

        if not args.data_package:
            raise ArgValueError('[ERR] Cannot pass None for pak_filename')

        if not args.redist:
            raise ArgValueError('[ERR] Cannot pass None for redist_filename')

        packager = Packager(args.project, args.i18n, args.data_package, args.redist, args.cfg, args.allow_arbitrary_files)

        if not os.path.exists(packager.manifest_path):
            raise ArgFileNotFoundError('[ERR] Cannot find mod.manifest in project root\n\t'
                                       'All mods require a manifest. Please create a mod.manifest file in the project root.')

        # create pak, if project has game data
        if os.path.exists(packager.project_data_path):
            Log.info('Starting PAK generation...', os.linesep)
            packager.generate_pak()
            Log.info('PAK generation complete.', os.linesep)
        else:
            Log.warn('Cannot find Data in project root. Skipping PAK generation.', os.linesep)

        # create localization paks, if project has localization
        if os.path.exists(packager.project_i18n_path):
            Log.info('Starting i18n generation...', os.linesep)
            packager.generate_i18n()
            Log.info('i18n generation complete.', os.linesep)
        else:
            Log.warn('Cannot find Localization in project root. Skipping PAK generation.', os.linesep)

        # create redistributable
        if os.path.exists(packager.redist_path):
            Log.info('Starting ZIP generation...', os.linesep)
            packager.pack()
            Log.info('ZIP generation complete.', os.linesep)
        else:
            raise ArgNotADirectoryError('[ERR] Cannot package mod because Build directory was not found\n\t'
                                        'Possible reasons:\n\t\t'
                                        '1. Project has no Data.\n\t\t'
                                        '2. Project has no Localization.')

    except (ArgFileNotFoundError, ArgNotADirectoryError, ArgValueError) as e:
        parser.print_help()
        print_exception(e)
        return

    except BaseException as e:
        print_exception(e)
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modsmith by fireundubh')
    parser.add_argument('-c', '--cfg', action='store', default='modsmith.conf', help='Path to modsmith.conf')
    parser.add_argument('-p', '--project', action='store', default=None, help='Input project path')
    parser.add_argument('-l', '--i18n', action='store', default=None, help='Input localization path')
    parser.add_argument('-d', '--data-package', action='store', default=None, help='Output PAK filename')
    parser.add_argument('-r', '--redist', action='store', default=None, help='Redistributable ZIP filename')
    parser.add_argument('--allow-arbitrary-files', action='store_true', default=False, help='Enable packing arbitrary files')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable logging tracebacks')
    args = parser.parse_args()
    main()
