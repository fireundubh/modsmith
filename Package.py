# coding=utf-8

import configparser
import glob
import os
import zipfile

from lxml import etree

from Utils import Utils


class Package:
    def __init__(self, project_path, pak_filename, redist_filename):
        self.project_path = project_path
        self.data_path = os.path.join(self.project_path, 'Data')
        self.data_filename = pak_filename
        self.data_xml_files = list()
        self.redist_filename = redist_filename
        self.redist_name = os.path.splitext(self.redist_filename)[0]
        self.redist_path = os.path.join(self.project_path, 'Build')
        self.redist_data_path = os.path.join(self.redist_path, self.redist_name, 'Data')
        self.i18n_project_path = os.path.join(self.project_path, 'Localization')
        self.i18n_redist_path = os.path.join(self.redist_path, self.redist_name, 'Localization')
        self.i18n_xml_files = list()
        self.manifest_path = os.path.join(self.project_path, 'mod.manifest')
        self.manifest_arcname = os.path.join(self.redist_name, 'mod.manifest')
        self.manifest = [self.manifest_path, self.manifest_arcname]
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app.conf'))

    def generate_pak(self):
        os.makedirs(self.redist_data_path, exist_ok=True)

        files = [f for f in glob.glob(os.path.join(self.data_path, '**\*'), recursive=True) if os.path.isfile(f)]
        for file in files:
            if file.endswith('.xml'):
                self.data_xml_files.append(file)

        self.patch_data()

        redist_pak_path = os.path.join(self.redist_data_path, self.data_filename)
        with zipfile.ZipFile(redist_pak_path, 'w', zipfile.ZIP_STORED) as zip_file:
            non_xml_files = [f for f in files if not f.endswith('.xml')]
            for file in non_xml_files:
                zip_file.write(file, file.replace(self.data_path, ''))
            for file in self.data_xml_files:
                zip_file.write(file.replace(self.data_path, self.redist_data_path), file.replace(self.data_path, ''))

        print('Wrote package:\t%s' % redist_pak_path)

    def generate_i18n(self):
        language_paths = os.listdir(self.i18n_project_path)

        for lang in language_paths:
            lang_path = os.path.join(self.i18n_redist_path, lang)
            os.makedirs(lang_path, exist_ok=True)

            files = glob.glob(os.path.join(self.i18n_project_path, lang, '*.xml'), recursive=False)
            for file in files:
                self.i18n_xml_files.append(file)

        self.patch_i18n()

        for lang in language_paths:
            lang_path = os.path.join(self.i18n_redist_path, lang)

            with zipfile.ZipFile(lang_path + '.pak', 'w', compression=zipfile.ZIP_STORED) as zip_file:
                files = glob.glob(os.path.join(lang_path, '*.xml'), recursive=False)
                for file in files:
                    zip_file.write(file, file.replace(os.path.join(self.i18n_redist_path, lang), ''))

    def pack(self):
        zip_archive = os.path.join(self.redist_path, self.redist_filename)

        with zipfile.ZipFile(zip_archive, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            print('Packaging file: %s (as %s)' % (self.manifest_path, self.manifest_arcname))
            zip_file.write(*self.manifest)

            files = glob.glob(os.path.join(self.redist_path, self.redist_name, '**\*.pak'), recursive=True)
            for file in files:
                arcname = file.replace(self.redist_path, '')
                print('Packaging file: %s (as %s)' % (file, arcname))
                zip_file.write(file, arcname)

        print('Wrote archive:\t%s' % zip_archive)

    def patch_data(self):
        # cull project path from xml file list
        xml_files = Utils.setup_xml_files(self.data_path, self.data_xml_files)

        for xml_file in xml_files:
            xml_data = Utils.setup_xml_data(self.data_path, xml_file)

            # determine which pak to read based on xml file path - requires a dictionary in Utils
            pak_file_name = Utils.get_pak_by_path(xml_data['xml_path'])
            if not pak_file_name:
                raise NotImplemented('Could not find pak based on file path: ', xml_data['xml_path'])

            # determine which key to read based on xml file name - requires a dictionary in Utils
            row_key = Utils.get_key_by_filename(xml_file[1])
            if not row_key:
                raise NotImplemented('Could not find key based on file name: ', xml_file[1])

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
                        output_rows = output_xml.findall(f"table/rows/row[@{row_key}='{input_row.get(row_key)}']")
                        if len(output_rows) > 1:
                            raise NotImplemented('Found more than one output row, probably a duplicate: ', output_rows)

                        # if the row with key exists, remove the row and add the input row
                        # else assume the input row is new and add the row to the output
                        if output_rows:
                            output_xml[0][1].remove(output_rows[0])
                            output_xml[0][1].append(input_row)
                        else:
                            output_xml[0][1].append(input_row)

                    # write output xml
                    Utils.write_output_xml(output_xml, os.path.join(self.redist_data_path, *xml_file))

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
            Utils.write_output_xml(output_xml, os.path.join(self.i18n_redist_path, *xml_file))
