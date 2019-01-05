# coding=utf-8

import argparse
import os

from modules.Packager import Packager


def main():
    try:
        if not os.path.exists('modsmith.conf'):
            if not args.cfg or args.cfg and not os.path.exists(args.cfg):
                raise FileNotFoundError('[ERR] Cannot find modsmith.conf\n\t'
                                        'Possible reasons:\n\t\t'
                                        '1. The modsmith.conf file does not exist in the Modsmith install path.\n\t\t'
                                        '2. The working directory was not set to the Modsmith install path.')

        if not args.project:
            raise ValueError('[ERR] Cannot pass None for project_path')

        if not args.data_package:
            raise ValueError('[ERR] Cannot pass None for pak_filename')

        if not args.redist:
            raise ValueError('[ERR] Cannot pass None for redist_filename')

        packager = Packager(args.project, args.i18n, args.data_package, args.redist, args.cfg)

        if not os.path.exists(packager.manifest_path):
            raise FileNotFoundError('[ERR] Cannot find mod.manifest in project root\n\t'
                                    'All mods require a manifest. Please create a mod.manifest file in the project root.')

        # create pak, if project has game data
        if os.path.exists(packager.project_data_path):
            packager.generate_pak()
        else:
            print('\n[WARN] Cannot find Data in project root. Skipping PAK generation.')

        # create localization paks, if project has localization
        if os.path.exists(packager.project_i18n_path):
            packager.generate_i18n()
        else:
            print('\n[WARN] Cannot find Localization in project root. Skipping PAK generation.')

        # create redistributable
        if os.path.exists(packager.redist_path):
            packager.pack()
        else:
            raise NotADirectoryError('[ERR] Cannot package mod because Build directory was not found\n\t'
                                     'Possible reasons:\n\t\t'
                                     '1. Project has no Data.\n\t\t'
                                     '2. Project has no Localization.')
    except BaseException as e:
        parser.print_help()

        if args.debug:
            import traceback
            print('%s%s' % (os.linesep, traceback.format_exc()))
        else:
            print('%s%s%s' % (os.linesep, e, os.linesep))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modsmith by fireundubh')
    parser.add_argument('-c', '--cfg', action='store', default='modsmith.conf', help='Path to modsmith.conf')
    parser.add_argument('-p', '--project', action='store', default=None, help='Input project path')
    parser.add_argument('-l', '--i18n', action='store', default=None, help='Input localization path')
    parser.add_argument('-d', '--data-package', action='store', default=None, help='Output PAK filename')
    parser.add_argument('-r', '--redist', action='store', default=None, help='Redistributable ZIP filename')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable traceback logging')
    args = parser.parse_args()
    main()
