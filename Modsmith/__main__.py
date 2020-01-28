import argparse

from modsmith import HelpFormatterEx
from modsmith.Application import Application

if __name__ == '__main__':
    _parser = argparse.ArgumentParser(description='Modsmith',
                                      formatter_class=HelpFormatterEx)

    _parser.add_argument('manifest_path',
                         metavar='<path>', nargs=1,
                         action='store', type=str,
                         help='path to mod.manifest in project root')

    _parser.add_argument('--pack-assets',
                         action='store_true', default=False,
                         help='add unsupported assets to package')

    _parser.add_argument('--debug',
                         action='store_true', default=False,
                         help='enable debug logging')

    Application(_parser.parse_args()).run()
