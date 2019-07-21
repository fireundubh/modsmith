import os
import posixpath
from typing import Generator

import regex
from contracts import contract, disable_all

from Modsmith.Constants import PRODUCTION

if PRODUCTION:
    disable_all()


class Common:
    @staticmethod
    @contract(path=str, files=list)
    def setup_xml_files(path: str, files: list) -> Generator:
        for file in files:
            relative_path = os.path.relpath(file, path)
            file_name, file_ext = os.path.split(relative_path)

            yield (file_name, file_ext, relative_path)

    @staticmethod
    @contract(string=str)
    def fix_slashes(string: str) -> str:
        """Return string with back slashes converted to forward slashes"""
        if '\\' in string:
            return posixpath.join(*string.split('\\'))
        return string

    @staticmethod
    @contract(text=str)
    def strip_whitespace(text: str) -> str:
        """Removes whitespace from string"""
        return text if not text or ' ' not in text else regex.sub('\s+', ' ', text).strip()

    @staticmethod
    @contract(xml_path=str, project_path=str, package_map=dict)
    def get_pak_by_path(xml_path: str, project_path: str, package_map: dict) -> str:
        relpath: str = Common.fix_slashes(os.path.relpath(xml_path, project_path))

        for path in package_map:
            if relpath.startswith(path):
                return package_map[path]

        raise FileNotFoundError('Cannot find PAK file by path: {}'.format(relpath))

    @staticmethod
    @contract(path=str, signatures=list)
    def get_signature_by_path(path: str, signatures: list) -> tuple:
        path = Common.fix_slashes(path)

        for i, key in enumerate(signatures):
            signature_key: str = next(iter(key))

            if not path.endswith(signature_key):
                continue

            signature: dict = signatures[i][signature_key][0]
            return signature['element'], signature['attributes']

        raise NotImplementedError('Cannot find signature by path: {}'.format(path))
