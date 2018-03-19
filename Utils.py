# coding=utf-8

import os
import re

from lxml import etree

from Database import DATA_MAP, SIGNATURES


class Utils:
    @staticmethod
    def setup_xml_files(path, files):
        """
        Sets up the list of files to be patched

        :param path: Path to remove from the file path
        :param files: List of absolute file paths to process
        :return: List of tuples
        """
        return [os.path.split(os.path.relpath(f, path)) for f in files]

    @staticmethod
    def setup_xml_data(path, file):
        """
        Sets up the data used to patch XML files

        :param path: Directory in which to find the XML file
        :param file: XML file with immediate parent directory
        :return: Dictionary of XML paths and rows
        """
        xml_path = os.path.join(path, *file)
        xml = etree.parse(xml_path, etree.XMLParser(remove_blank_text=True)).getroot()
        rows = xml.findall('table/rows/row') or xml.findall('Row')
        return {'xml_path': xml_path, 'xml_rows': rows}

    @staticmethod
    def write_output_xml(xml_data, file_path, i18n=False):
        """
        Writes XML data to output XML file

        :param xml_data: XML data to write out
        :param file_path: Path to output file
        :param i18n: Boolean indicating file format
        :return: None
        """
        if i18n:
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(etree.tostring(xml_data, pretty_print=True).decode('unicode-escape'))
        else:
            et = etree.ElementTree(xml_data)
            et.write(file_path, encoding='us-ascii', xml_declaration=True, pretty_print=True)

    @staticmethod
    def strip_whitespace(text):
        """
        Removes extra whitespace from text, such as double spaces

        :param text: String to be stripped of extra whitespace
        :return: String
        """
        if text:
            text = re.sub('\s+', ' ', text)
            return text.strip()

    @staticmethod
    def get_signature_by_filename(filename, *, keymap=SIGNATURES):
        """
        Retrieves the signature of an XML row based on file name

        :param filename: File name to look up as key in dictionary
        :param keymap: (optional) Dictionary of signatures
        :return: String or list
        """
        file_name, file_ext = os.path.splitext(filename)
        for key in keymap.keys():
            if key == file_name:
                return keymap[key]

    @staticmethod
    def get_pak_by_path(xml_path):
        """
        Retrieves the source PAK by file path

        :param xml_path: Relative path to XML file (e.g., Data\Libs\Tables\rpg\rpg_param.xml)
        :return: PAK file name with extension (e.g., Tables.pak)
        """
        for key in DATA_MAP.keys():
            if key in xml_path:
                return DATA_MAP[key]
