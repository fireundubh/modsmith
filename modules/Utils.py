import os
import re
import types

from lxml import etree

from modules.Database import DATA_MAP

XML_PARSER = etree.XMLParser(remove_blank_text=True)


class Utils:
    @staticmethod
    def setup_xml_files(path: str, files: iter) -> types.GeneratorType:
        for file in files:
            relative_path = os.path.relpath(file, path)
            yield tuple([*os.path.split(relative_path), relative_path])

    @staticmethod
    def strip_whitespace(text: str) -> str:
        if text:
            return re.sub('\s+', ' ', text).strip()

    @staticmethod
    def get_pak_by_path(xml_path: str, *, keymap: dict = DATA_MAP, project_path: str):
        for key in keymap.keys():
            if os.path.relpath(xml_path, project_path).startswith(key):
                return keymap[key]
