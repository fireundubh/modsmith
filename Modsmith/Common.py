import os
import posixpath

import regex


class Common:
    @staticmethod
    def fix_slashes(string: str) -> str:
        """Return string with back slashes converted to forward slashes"""
        if '\\' in string:
            return posixpath.join(*string.split('\\'))
        return string

    @staticmethod
    def strip_whitespace(string: str) -> str:
        """Removes whitespace from string"""
        return string if not string or ' ' not in string else regex.sub('\s+', ' ', string).strip()

    @staticmethod
    def get_pak_by_path(xml_path: str, project_path: str, package_map: dict) -> str:
        """
        Retrieves game PAK file name with extension from relative path.

        Raises FileNotFoundError if the relative path does not map to a file name.
        """
        relpath: str = Common.fix_slashes(os.path.relpath(xml_path, project_path))

        for path in package_map:
            if relpath.startswith(path):
                return package_map[path]

        raise FileNotFoundError(f'Cannot find PAK file by path: {relpath}')

    @staticmethod
    def get_signature_by_path(path: str, signatures: list) -> tuple:
        """
        Retrieves element signature from path.

        Raises ``NotImplementedError`` if path not found in signatures map.
        """
        path = Common.fix_slashes(path)

        for i, key in enumerate(signatures):
            signature_key: str = next(iter(key))

            if not path.endswith(signature_key):
                continue

            signature: dict = signatures[i][signature_key][0]
            return signature['element'], signature['attributes']

        raise NotImplementedError(f'Cannot find signature by path: {path}')
