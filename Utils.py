# coding=utf-8

import os
import re

from lxml import etree

from Database import DATA_MAP, SIGNATURES


class Utils:
    @staticmethod
    def strip_whitespace(text):
        if text:
            text = re.sub('\s+', ' ', text)
            return text.strip()

    @staticmethod
    def get_signature_by_filename(filename, *, keymap=SIGNATURES):
        file_name, file_ext = os.path.splitext(filename)
        for key in keymap.keys():
            if key == file_name:
                return keymap[key]

    @staticmethod
    def get_pak_by_path(xml_path):
        for key in DATA_MAP.keys():
            if key in xml_path:
                return DATA_MAP[key]

    @staticmethod
    def setup_xml_files(path, files):
        return [os.path.split(f.replace(path + '\\', '')) for f in files]

    @staticmethod
    def setup_xml_data(path, file):
        xml_path = os.path.join(path, *file)
        xml = etree.parse(xml_path, etree.XMLParser(remove_blank_text=True)).getroot()
        rows = xml.findall('table/rows/row') or xml.findall('Row')
        return {'xml_path': xml_path, 'xml_rows': rows}

    @staticmethod
    def write_output_xml(xml_data, file_path, i18n=False):
        if i18n:
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(etree.tostring(xml_data, pretty_print=True).decode('unicode-escape'))
        else:
            et = etree.ElementTree(xml_data)
            et.write(file_path, encoding='us-ascii', xml_declaration=True, pretty_print=True)
