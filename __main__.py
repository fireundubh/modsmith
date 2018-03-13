# coding=utf-8

import argparse
import os
import sys

from Package import Package


def main():
    if not os.path.exists('modsmith.conf'):
        sys.tracebacklimit = 0
        raise FileNotFoundError('Cannot find modsmith.conf, exiting')

    package = Package(args.project, args.data_package, args.redist)
    package.generate_pak()
    package.generate_i18n()
    package.pack()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Modsmith by fireundubh')
    parser.add_argument('-p', '--project', action='store', required=True, default=None, help='Input project path')
    parser.add_argument('-d', '--data-package', action='store', required=True, default=None, help='Output PAK filename')
    parser.add_argument('-r', '--redist', action='store', required=True, default=None, help='Redistributable ZIP filename')
    args = parser.parse_args()
    main()
