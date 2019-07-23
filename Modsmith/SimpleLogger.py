import sys

from colorama import Fore


class SimpleLogger:
    @staticmethod
    def error(message: str, *, prefix: str = '', suffix: str = '') -> None:
        print('%s%s[%s] %s%s%s' % (prefix, Fore.RED, 'ERRO', message, suffix, Fore.RESET))

    @staticmethod
    def info(message: str, *, prefix: str = '', suffix: str = '') -> None:
        print('%s[%s] %s%s' % (prefix, 'INFO', message, suffix))

    @staticmethod
    def warn(message: str, *, prefix: str = '', suffix: str = '') -> None:
        print('%s%s[%s] %s%s%s' % (prefix, Fore.YELLOW, 'WARN', message, suffix, Fore.RESET))

    @staticmethod
    def debug(message: str, *, prefix: str = '', suffix: str = '') -> None:
        if '--debug' in sys.argv:
            print('%s%s[%s] %s%s%s' % (prefix, Fore.CYAN, 'DEBUG', message, suffix, Fore.RESET))
