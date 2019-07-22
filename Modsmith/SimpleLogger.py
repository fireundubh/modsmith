import colorama
import sys
from colorama import Fore

from Modsmith.Constants import PRODUCTION


class SimpleLogger:
    def __init__(self) -> None:
        colorama.init()

    @staticmethod
    def error(message: str, *, prefix: str = '', suffix: str = '') -> None:
        print('%s%s[%s] %s%s%s' % (Fore.RED, prefix, 'ERRO', message, suffix, Fore.RESET))

    @staticmethod
    def info(message: str, *, prefix: str = '', suffix: str = '') -> None:
        print('%s[%s] %s%s' % (prefix, 'INFO', message, suffix))

    @staticmethod
    def warn(message: str, *, prefix: str = '', suffix: str = '') -> None:
        print('%s%s[%s] %s%s%s' % (Fore.YELLOW, prefix, 'WARN', message, suffix, Fore.RESET))

    @staticmethod
    def debug(message: str, *, prefix: str = '', suffix: str = '') -> None:
        if not PRODUCTION or PRODUCTION and '--debug' in sys.argv:
            print('%s%s[%s] %s%s%s' % (Fore.CYAN, prefix, 'DEBUG', message, suffix, Fore.RESET))
