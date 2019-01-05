class SimpleLogger:
    @staticmethod
    def error(message, prefix='', suffix=''):
        print('%s[%s] %s%s' % (prefix, 'ERRO', message, suffix))

    @staticmethod
    def info(message, prefix='', suffix=''):
        print('%s[%s] %s%s' % (prefix, 'INFO', message, suffix))

    @staticmethod
    def warn(message, prefix='', suffix=''):
        print('%s[%s] %s%s' % (prefix, 'WARN', message, suffix))
