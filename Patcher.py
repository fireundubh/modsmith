# coding=utf-8

import os
import zipfile

from lxml import etree

from Utils import Utils


class Patcher:
    def __init__(self, package):
        self.config = package.config
        self.data_path = package.data_path
        self.data_xml_files = package.data_xml_files

        self.redist_data_path = package.redist_data_path
        self.redist_path = package.redist_path

        self.i18n_project_path = package.i18n_project_path
        self.i18n_redist_path = package.i18n_redist_path
        self.i18n_xml_files = package.i18n_xml_files

    def patch_data(self):
        # cull project path from xml file list
        xml_files = Utils.setup_xml_files(self.data_path, self.data_xml_files)

        for xml_file in xml_files:
            xml_data = Utils.setup_xml_data(self.data_path, xml_file)

            # determine which pak to read based on xml file path - requires a dictionary in Utils
            pak_file_name = Utils.get_pak_by_path(xml_data['xml_path'])
            if not pak_file_name:
                raise Exception('Cannot find PAK based on file path: ', xml_data['xml_path'])

            # determine which key to read based on xml file name - requires a dictionary in Utils
            signature = Utils.get_signature_by_filename(xml_file[1])
            if not signature:
                raise Exception('Cannot find signature based on file path: ', xml_file[1])

            # load pak
            game_data_path = os.path.join(self.config['Game']['Path'], 'Data', pak_file_name)

            with zipfile.ZipFile(game_data_path, mode='r') as pak_file:
                # get arcname of file in archive (e.g., Libs/Tables/rpg/buff.xml)
                packed_file = os.path.join(xml_data['xml_path'].replace(self.data_path, '')).replace('\\', '/').lstrip('/')

                # read file in archive
                with pak_file.open(packed_file, 'r') as pak_xml:
                    lines = pak_xml.readlines()
                    output_xml = etree.fromstringlist(lines, etree.XMLParser(remove_blank_text=True))

                    # merge rows
                    for input_row in xml_data['xml_rows']:
                        # determine whether a row with the key already exists
                        if isinstance(signature, str):
                            output_rows = output_xml.findall(f"table/rows/row[@{signature}='{input_row.get(signature)}']")
                            if len(output_rows) > 1:
                                raise Exception('Found more than one output row. Reason: Duplicate or bad signature.', output_rows)
                        elif isinstance(signature, list):
                            # create xpath expression for list of keys
                            xpath = []
                            for i in range(0, len(signature)):
                                xpath.append(f'@{signature[i]}="{input_row.get(signature[i])}"')
                            output_rows = output_xml.xpath('table/rows/row[%s]' % ' and '.join(xpath))
                        else:
                            raise Exception('Something weird happened!')

                        # if the row with key exists, remove the row and add the input row
                        # else assume the input row is new and add the row to the output
                        if output_rows is not None and len(output_rows) != 0:
                            output_xml[0][1].remove(output_rows[0])
                            output_xml[0][1].append(input_row)
                        else:
                            output_xml[0][1].append(input_row)

                    # write output xml
                    Utils.write_output_xml(output_xml, os.path.join(self.redist_data_path, *xml_file), False)

    def patch_i18n(self):
        # cull project path from xml file list
        xml_files = Utils.setup_xml_files(self.i18n_project_path, self.i18n_xml_files)

        # read game localization files
        for xml_file in xml_files:
            xml_data = Utils.setup_xml_data(self.i18n_project_path, xml_file)

            # create output xml
            output_xml = etree.Element('Table')
            for row in xml_data['xml_rows']:
                output_xml.append(row)

            # create row data for comparing keys
            row_keys = []
            for row in output_xml:
                key, original_text, translated_text = [r for r in row.findall('Cell')]
                row_keys.append(key.text)
            if not row_keys:
                raise Exception('row_keys empty')

            # read zipped pak xml
            lang_pak_path = os.path.join(self.config['Game']['Path'], 'Localization', xml_file[0] + '.pak')
            with zipfile.ZipFile(lang_pak_path, mode='r') as pak_file:
                with pak_file.open(xml_file[1], mode='r') as pak_xml:
                    lines = pak_xml.readlines()
                    xml = etree.fromstringlist(lines, etree.XMLParser(remove_blank_text=True))
                    rows = xml.findall('Row')

                    for row in rows:
                        key, original_text, translated_text = [r for r in row.findall('Cell')]

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
            Utils.write_output_xml(output_xml, os.path.join(self.i18n_redist_path, *xml_file), True)
