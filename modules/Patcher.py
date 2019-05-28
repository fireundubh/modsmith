import copy
import os
import types

from lxml import etree

from modules.Database import Database
from modules.Package import Package
from modules.SimpleLogger import SimpleLogger as Log
from modules.Utils import Utils
from stdlib.zipfilePatch import ZipFileFixed

XML_PARSER = etree.XMLParser(encoding='utf-8', remove_blank_text=True, strip_cdata=False)


class Patcher(Package):
    def __init__(self, project_path, project_i18n_path, output_pak_file_name, redist_file_name, cfg_path):
        super(Patcher, self).__init__(project_path, project_i18n_path, output_pak_file_name, redist_file_name, cfg_path)

    @staticmethod
    def _get_string_keys(rows: etree.ElementTree) -> types.GeneratorType:
        for row in rows:
            key, _, _ = row.findall('Cell')
            yield key.text

    @staticmethod
    def _merge_rows(rows: etree.ElementTree, signatures: tuple, output_xml: etree.ElementTree) -> None:
        for source_row in rows:
            xpaths = [f'@{signature}="{source_row.get(signature)}"' for signature in signatures]
            output_rows = output_xml.xpath(f'table/rows/row[{" and ".join(xpaths)}]')

            for output_row in output_rows:
                output_xml[0][1].remove(output_row)
                output_xml[0][1].append(source_row)
            else:
                output_xml[0][1].append(source_row)

    @staticmethod
    def _merge_string_rows(rows: etree.ElementTree, signatures: tuple, output_xml: etree.ElementTree) -> None:
        for row in rows:
            key, _, _ = row.findall('Cell')

            if key.text in signatures:
                continue

            # we've already added our strings, so merge the unmodified strings
            for i in range(0, 3):
                row[i].text = Utils.strip_whitespace(row[i].text)

            output_xml.append(row)

    def patch_data(self, xml_file_list: set) -> None:
        """
        Copies source, replaces existing rows with modified rows, and appends assumed new rows that cannot be found in source.
        Writes out XML to file in the redistributable path.

        :param xml_file_list: List of XML files to be patched
        """
        for parent_path, xml_file_name, relative_xml_path in Utils.setup_xml_files(self.project_data_path, xml_file_list):
            project_xml_path = os.path.join(self.project_data_path, relative_xml_path)

            Log.info('Patching XML file:\t%s (source: %s)' % (relative_xml_path, project_xml_path))

            pak_file_name = Utils.get_pak_by_path(project_xml_path, project_path=self.project_path)
            zipped_pak_path = os.path.join(self.config['Game']['Path'], 'Data', pak_file_name)

            arc_name = relative_xml_path.replace(os.path.sep, os.path.altsep)

            # read zipped pak xml
            with ZipFileFixed(zipped_pak_path, mode='r') as data:
                with data.open(arc_name, 'r') as xml:
                    lines = xml.readlines()

            output_xml = etree.fromstringlist(lines, XML_PARSER)

            # merge rows based on signature lookup
            rows = etree.parse(project_xml_path, XML_PARSER).getroot().findall('table/rows/row')
            signatures = Database.get_signatures()
            self._merge_rows(rows, signatures[xml_file_name[:-4]], output_xml)

            redist_xml_path = os.path.join(self.redist_data_path, parent_path, xml_file_name)
            etree.ElementTree(output_xml, parser=XML_PARSER).write(redist_xml_path, encoding='utf-8', pretty_print=True, xml_declaration=True)

    # TODO: support patching localization strings from XLSX and JSON sources
    def patch_i18n(self, xml_file_list: iter) -> None:
        """
        Constructs XML in memory, seeds with modified rows, and appends unmodified source rows.
        Writes out XML to file in the redistributable path.

        :param xml_file_list: List of XML files to be patched
        """
        # filter out unsupported xml files - we can arbitrarily add these later but we can't patch them
        supported_xml_files = Database.get_localization()
        xml_file_list = [x for x in xml_file_list if os.path.basename(x) in supported_xml_files]

        for parent_path, file_name, relative_xml_path in Utils.setup_xml_files(self.project_i18n_path, xml_file_list):
            project_xml_path = os.path.join(self.project_i18n_path, relative_xml_path)

            Log.info('Patching XML file:\t%s (source: %s)' % (relative_xml_path, project_xml_path))

            source_rows = etree.parse(project_xml_path, XML_PARSER).getroot().findall('Row')

            # create output xml
            output_xml = etree.Element('Table')

            # if there is only one text cell, clone that cell
            # this allows users to, optionally, maintain simpler localization xml files
            for row in source_rows:
                if len(row) == 2:
                    key, original_text = row.findall('Cell')
                    translated_text = copy.deepcopy(original_text)
                    row.append(translated_text)

                output_xml.append(row)

            # read zipped pak xml
            zip_path = os.path.join(self.config['Game']['Path'], 'Localization', parent_path + '.pak')

            if not os.path.exists(zip_path):
                Log.warn('Cannot patch XML file using archive. File does not exist:\t%s' % zip_path)
                continue

            with ZipFileFixed(zip_path, mode='r') as data:
                with data.open(file_name, mode='r') as xml:
                    lines = xml.readlines()

            output_rows = etree.fromstringlist(lines, XML_PARSER).findall('Row')

            # create row data for comparing keys
            signatures = tuple(set(self._get_string_keys(output_xml)))

            self._merge_string_rows(output_rows, signatures, output_xml)

            # sort output xml by key
            tree = output_xml.findall('Row')
            output_xml[:] = sorted(tree, key=lambda r: r.xpath('Cell/text()'))

            redist_xml_path = os.path.join(self.redist_i18n_path, relative_xml_path)

            with open(redist_xml_path, mode='w', encoding='utf-8'):
                et = etree.ElementTree(output_xml, parser=XML_PARSER)
                et.write(redist_xml_path, encoding='utf-8', pretty_print=True)
