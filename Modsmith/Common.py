import posixpath


def fix_slashes(string: str) -> str:
    """Return string with back slashes converted to forward slashes"""
    if '\\' in string:
        return posixpath.join(*string.split('\\'))
    return string


def to_version(text) -> tuple:
    filled = []
    for dot in text.split('.'):
        filled.append(dot.zfill(8))
    return tuple(filled)
