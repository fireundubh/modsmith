import copy
import os

from contracts import contract, disable_all
from lxml import etree

from Modsmith.Common import Common
from Modsmith.Constants import PRODUCTION, ROW_XPATH, XML_PARSER
from Modsmith.Extensions import ZipFileFixed
from Modsmith.ProjectSettings import ProjectSettings
from Modsmith.SimpleLogger import SimpleLogger as Log

if PRODUCTION:
    disable_all()


# noinspection PyProtectedMember
class Patcher:
    def __init__(self, settings: ProjectSettings) -> None:
        self.settings: ProjectSettings = settings

    @staticmethod
    @contract(elements=etree._Element)
    def _get_string_keys(elements: etree._Element) -> set:
        results: set = set()
        for element in elements:
            results.add(list(element)[0].text)
        return results

    @staticmethod
    @contract(elements=list, signatures=tuple, output_xml=etree._Element)
    def _merge_rows(elements: list, signatures: tuple, output_xml: etree._Element) -> None:
        element_name, element_attributes = signatures

        for element in elements:
            attrs: str = ' and '.join([f'@{key}="{element.get(key)}"' for key in sorted(element_attributes)])
            output_rows: list = output_xml.xpath('//%s[%s]' % (element_name, attrs))

            for output_row in output_rows:
                output_xml[0][1].remove(output_row)
                output_xml[0][1].append(element)
            else:
                output_xml[0][1].append(element)

    @staticmethod
    @contract(elements=list, signatures=set, output_xml=etree._Element)
    def _merge_string_rows(elements: list, signatures: set, output_xml: etree._Element) -> None:
        for element in elements:
            cells: list = list(element)

            if cells[0].text in signatures:
                continue

            # we've already added our strings, so merge the unmodified strings
            for i in range(0, 3):
                cell_text: str = cells[i].text
                if cell_text:
                    cells[i].text = Common.strip_whitespace(cell_text)

            output_xml.append(element)

    @staticmethod
    @contract(rows=list, output_xml=etree._Element)
    def _try_clone_text_cells(rows: list, output_xml: etree._Element) -> None:
        """Clones text cell as translation cells if there are only two cells"""
        for row in rows:
            cells: list = list(row)

            if len(cells) == 2:
                original_text_clone: str = copy.deepcopy(cells[1])
                row.append(original_text_clone)

            output_xml.append(row)

    @contract(xml_file_list=list)
    def patch_data(self, xml_file_list: list) -> None:
        """
        Copies source, replaces existing rows with modified rows, and appends assumed new rows that cannot be found in source.

        Writes out XML to file in the build path.
        """

        for parent_path, xml_file_name, relative_xml_path in Common.setup_xml_files(self.settings.project_data_path, xml_file_list):
            project_xml_path: str = os.path.join(self.settings.project_data_path, relative_xml_path)

            Log.info('Patching XML file: {} (source: {})'.format(relative_xml_path, project_xml_path))

            pak_file_name: str = Common.get_pak_by_path(project_xml_path, self.settings.project_path, self.settings.packages)
            game_pak_path: str = os.path.join(self.settings.game_path, 'Data', pak_file_name)

            arc_name: str = relative_xml_path.replace(os.path.sep, os.path.altsep)

            # read zipped pak xml
            with ZipFileFixed(game_pak_path, mode='r') as data:
                with data.open(arc_name, 'r') as xml:
                    # we can't use etree.parse() because we need to replace elements in _merge_rows()
                    lines: list = xml.read().splitlines()

            output_xml = etree.fromstringlist(lines, XML_PARSER)

            # merge rows based on signature lookup
            project_xml_tree = etree.parse(project_xml_path, XML_PARSER)

            rows: list = project_xml_tree.xpath(ROW_XPATH)
            if not rows:
                raise NotImplementedError('Cannot find rows to merge in: {}'.format(project_xml_path))

            signatures: tuple = Common.get_signature_by_path(project_xml_path, self.settings.signatures)

            self._merge_rows(rows, signatures, output_xml)

            build_xml_file_path: str = os.path.join(self.settings.build_data_path, parent_path, xml_file_name)

            tree: etree._ElementTree = etree.ElementTree(output_xml, parser=XML_PARSER)
            tree.write(build_xml_file_path, encoding='utf-8', pretty_print=True, xml_declaration=True)

    @contract(xml_file_list=list)
    def patch_localization(self, xml_file_list: list) -> None:
        """
        Constructs XML in memory, seeds with modified rows, and appends unmodified source rows.

        Writes out XML to file in the redistributable path.
        """

        # filter out unsupported xml files - we can arbitrarily add these later but we can't patch them
        xml_file_list = [f for f in xml_file_list if os.path.basename(f) in self.settings.localization]

        for parent_path, file_name, relative_xml_path in Common.setup_xml_files(self.settings.project_localization_path, xml_file_list):
            project_xml_path: str = os.path.join(self.settings.project_localization_path, relative_xml_path)

            Log.info('Patching XML file: {} (source: {})'.format(relative_xml_path, project_xml_path))

            project_xml_tree: etree._ElementTree = etree.parse(project_xml_path, XML_PARSER)
            rows: list = project_xml_tree.xpath(ROW_XPATH)

            if not rows:
                raise NotImplementedError('Cannot find rows to patch in: {}'.format(project_xml_path))

            # create output xml
            output_xml: etree._Element = etree.Element('Table')
            self._try_clone_text_cells(rows, output_xml)

            # read zipped pak xml
            zip_path: str = os.path.join(self.settings.game_path, 'Localization', parent_path + '.pak')

            if not os.path.exists(zip_path):
                Log.warn('Cannot patch XML file using archive. File does not exist: {}'.format(zip_path))
                continue

            with ZipFileFixed(zip_path, mode='r') as data:
                with data.open(file_name, mode='r') as xml:
                    lines = xml.read().splitlines()

            game_tree: etree._ElementTree = etree.fromstringlist(lines, XML_PARSER)
            game_rows: list = game_tree.xpath(ROW_XPATH)

            # create row data for comparing keys
            signatures: set = self._get_string_keys(output_xml)

            self._merge_string_rows(game_rows, signatures, output_xml)

            # sort output xml by key
            rows = output_xml.xpath(ROW_XPATH)
            output_xml[:] = sorted(rows, key=lambda r: r.xpath('Cell/text()'))

            build_xml_path: str = os.path.join(self.settings.build_localization_path, relative_xml_path)

            with open(build_xml_path, mode='w', encoding='utf-8'):
                et: etree._ElementTree = etree.ElementTree(output_xml, parser=XML_PARSER)
                et.write(build_xml_path, encoding='utf-8', pretty_print=True)
