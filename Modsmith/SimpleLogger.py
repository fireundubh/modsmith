import colorama
from colorama import Fore


class SimpleLogger:
    def __init__(self) -> None:
        colorama.init()

    @staticmethod
    def error(message: str, prefix: str = '', suffix: str = '') -> None:
        print('%s%s[%s] %s%s%s' % (Fore.RED, prefix, 'ERRO', message, suffix, Fore.RESET))

    @staticmethod
    def info(message: str, prefix: str = '', suffix: str = '') -> None:
        print('%s[%s] %s%s' % (prefix, 'INFO', message, suffix))

    @staticmethod
    def warn(message: str, prefix: str = '', suffix: str = '') -> None:
        print('%s%s[%s] %s%s%s' % (Fore.YELLOW, prefix, 'WARN', message, suffix, Fore.RESET))
