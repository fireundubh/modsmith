import posixpath


class Common:
    @staticmethod
    def fix_slashes(string: str) -> str:
        """Return string with back slashes converted to forward slashes"""
        if '\\' in string:
            return posixpath.join(*string.split('\\'))
        return string
