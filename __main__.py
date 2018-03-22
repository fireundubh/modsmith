# coding=utf-8

import argparse
import os
import sys

from Packager import Packager


def main():
    if not os.path.exists('modsmith.conf'):
        sys.tracebacklimit = 0
        raise FileNotFoundError('Cannot find modsmith.conf\n'
                                '\tPossible reasons:\n'
                                '\t\t1. The modsmith.conf file does not exist in the Modsmith install path.\n'
                                '\t\t2. The working directory was not set to the Modsmith install path.')

    packager = Packager(args.project, args.data_package, args.redist)

    if not os.path.exists(packager.manifest_path):
        sys.tracebacklimit = 0
        raise FileNotFoundError('Cannot find mod.manifest in project root\n'
                                '\tAll mods require a manifest. Please create a mod.manifest file in the project root.')

    # create pak, if project has game data
    if os.path.exists(packager.data_path):
        packager.generate_pak()
    else:
        print('\n[WARN] Cannot find Data in project root. Skipping PAK generation.')

    # create localization paks, if project has localization
    if os.path.exists(packager.i18n_project_path):
        packager.generate_i18n()
    else:
        print('\n[WARN] Cannot find Localization in project root. Skipping PAK generation.')

    # create redistributable
    if os.path.exists(packager.redist_path):
        packager.pack()
    else:
        sys.tracebacklimit = 0
        raise NotADirectoryError('Cannot package mod because Build directory was not found\n'
                                 '\tPossible reasons:\n'
                                 '\t\t1. Project has no Data.\n'
                                 '\t\t2. Project has no Localization.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modsmith by fireundubh')
    parser.add_argument('-p', '--project', action='store', required=True, default=None, help='Input project path')
    parser.add_argument('-d', '--data-package', action='store', default=None, help='Output PAK filename')
    parser.add_argument('-r', '--redist', action='store', required=True, default=None, help='Redistributable ZIP filename')
    args = parser.parse_args()
    main()
