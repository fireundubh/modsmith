# coding=utf-8

import os
import re

from lxml import etree

DATA_MAP = {
    'Data\Libs\Tables': 'Tables.pak',
    'Data\Scripts': 'Scripts.pak',
    'Data\Libs': 'Scripts.pak',
    'Data\Entities': 'Scripts.pak'
}

KEY_MAP = {
    'buff.xml': 'buff_id',
    'buff_class.xml': 'buff_class_id',
    'buff_lifetime.xml': 'buff_lifetime_id',
    'perk.xml': 'perk_id',
    'perk_buff.xml': 'buff_id',
    'perk_buff_override.xml': 'perk_id',
    'perk_codex.xml': 'perk_id',
    'perk_combo_step.xml': 'perk_id',
    'perk_companion.xml': 'perk_id',
    'perk_recipe.xml': 'perk_id',
    'perk_script.xml': 'perk_id',
    'perk_soul_ability.xml': 'perk_id',
    'perk_special_riposte.xml': 'perk_id',
    'perk2perk_exclusivity.xml': 'first_perk_id'
}


class Utils:
    @staticmethod
    def strip_whitespace(text):
        if text:
            text = re.sub('\s+', ' ', text)
            return text.strip()

    @staticmethod
    def get_key_by_filename(filename):
        for key in KEY_MAP.keys():
            if key == filename:
                return KEY_MAP[key]

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
    def write_output_xml(xml_data, file_path):
        with open(file_path, 'w', encoding='utf8') as f:
            f.write(etree.tostring(xml_data, pretty_print=True).decode('unicode-escape'))
