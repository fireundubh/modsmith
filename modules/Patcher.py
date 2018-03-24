# coding=utf-8

import copy
import os
import zipfile

from lxml import etree

from modules.Database import EXCLUSIONS
from modules.Utils import Utils


class Patcher:
    def __init__(self, packager):
        """
        Sets up the necessary paths for patching XML files

        :param packager: Instance of the Packager class for the project
        """
        self.config = packager.config
        self.data_path = packager.data_path

        self.redist_data_path = packager.redist_data_path
        self.redist_path = packager.redist_path

        self.i18n_project_path = packager.i18n_project_path
        self.i18n_redist_path = packager.i18n_redist_path

    def patch_data(self, xml_file_list):
        """
        Copies source, replaces existing rows with modified rows, and appends assumed new rows that cannot be found in source.
        Writes out XML to file in the redistributable path.

        :param xml_file_list: List of XML files to be patched
        """

        # cull excluded paths from xml file list
        supported_xml_files = [f for f in xml_file_list if not any(x in f for x in EXCLUSIONS)]

        # cull project path from xml file list
        xml_files = Utils.setup_xml_files(self.data_path, supported_xml_files)

        for xml_file in xml_files:
            xml_data = Utils.setup_xml_data(self.data_path, xml_file)

            # determine which pak to read based on xml file path - requires a dictionary in Utils
            pak_file_name = Utils.get_pak_by_path(xml_data['xml_path'])

            if not pak_file_name:
                raise Exception('Cannot find PAK based on file path', xml_data['xml_path'])

            # determine which key to read based on xml file name - requires a dictionary in Utils
            signature = Utils.get_signature_by_filename(xml_file[1])

            if not signature:
                raise Exception('Cannot find signature based on file name', xml_file[1])

            # load pak
            game_data_path = os.path.join(self.config['Game']['Path'], 'Data', pak_file_name)

            with zipfile.ZipFile(game_data_path, mode='r') as pak_file:
                # get arcname of file in archive (e.g., Libs/Tables/rpg/buff.xml)
                packed_file = os.path.join(os.path.relpath(xml_data['xml_path'], self.data_path)).replace(os.path.sep, '/')

                # read file in archive
                with pak_file.open(packed_file, 'r') as pak_xml:
                    output_xml = etree.fromstringlist(pak_xml.readlines(), etree.XMLParser(remove_blank_text=True))

                    # merge rows
                    for input_row in xml_data['xml_rows']:
                        # determine whether a row with the key already exists
                        if isinstance(signature, str):
                            output_rows = output_xml.findall(f"table/rows/row[@{signature}='{input_row.get(signature)}']")
                            if len(output_rows) > 1:
                                raise Exception('Found more than one output row\n'
                                                '\tPossible reasons:\n'
                                                '\t\t1. There was a duplicate row in the XML source.\n'
                                                '\t\t2. The signature used to find unique rows was too broad.')
                        elif isinstance(signature, list):
                            # create xpath expression for list of keys
                            xpaths = [f'@{signature[i]}="{input_row.get(signature[i])}"' for i in range(0, len(signature))]
                            output_rows = output_xml.xpath('table/rows/row[%s]' % ' and '.join(xpaths))
                        else:
                            # this should never happen, but continue with error
                            print('\n[ERROR] Found signature was not str or list. Actual type:', type(signature))
                            continue

                        # if the row with key exists, remove the row and add the input row
                        # else assume the input row is new and add the row to the output
                        if output_rows is not None and len(output_rows) != 0:
                            output_xml[0][1].remove(output_rows[0])
                            output_xml[0][1].append(input_row)
                            continue

                        output_xml[0][1].append(input_row)

                    # write output xml
                    Utils.write_xml(output_xml, os.path.join(self.redist_data_path, *xml_file), False)

    # TODO: support patching localization strings from XLSX and JSON sources
    def patch_i18n(self, xml_file_list):
        """
        Constructs XML in memory, seeds with modified rows, and appends unmodified source rows.
        Writes out XML to file in the redistributable path.

        :param xml_file_list: List of XML files to be patched
        """

        # cull project path from xml file list
        xml_files = Utils.setup_xml_files(self.i18n_project_path, xml_file_list)

        # read game localization files
        for xml_file in xml_files:
            xml_data = Utils.setup_xml_data(self.i18n_project_path, xml_file)

            # create output xml
            output_xml = etree.Element('Table')

            for row in xml_data['xml_rows']:
                # if there is only one text cell, clone that cell
                # this allows users to, optionally, maintain simpler localization xml files
                if len(row) == 2:
                    key, original_text = [c for c in row.findall('Cell')]
                    translated_text = copy.deepcopy(original_text)
                    row.append(translated_text)
                output_xml.append(row)

            # create row data for comparing keys
            row_keys = []

            for row in output_xml:
                cells = row.findall('Cell')
                key, original_text, translated_text = [c for c in cells]
                row_keys.append(key.text)

            if not row_keys:
                raise Exception('row_keys empty')

            # read zipped pak xml
            lang_pak_path = os.path.join(self.config['Game']['Path'], 'Localization', xml_file[0] + '.pak')

            with zipfile.ZipFile(lang_pak_path, mode='r') as pak_file:
                with pak_file.open(xml_file[1], mode='r') as pak_xml:
                    xml = etree.fromstringlist(pak_xml.readlines(), etree.XMLParser(remove_blank_text=True))
                    rows = xml.findall('Row')

                    for row in rows:
                        key, original_text, translated_text = [r for r in row.findall('Cell')]

                        if key.text in row_keys:
                            continue

                        # we've already added our strings, so merge the unmodified strings
                        if key.text not in row_keys:
                            # strip leading and trailing whitespace from cells
                            # strip unnecessary whitespace from within cells
                            for i in range(0, 3):
                                row[i].text = Utils.strip_whitespace(row[i].text)

                            # add row to output xml
                            output_xml.append(row)

            # sort output xml by key
            tree = output_xml.findall('Row')
            output_xml[:] = sorted(tree, key=lambda x: x.xpath('Cell/text()'))

            # write output xml
            Utils.write_xml(output_xml, os.path.join(self.i18n_redist_path, *xml_file), True)
