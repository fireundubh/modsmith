import copy
import os
import re
from functools import partial

from lxml import etree

from Modsmith.Common import Common
from Modsmith.Constants import PRECOMPILED_XPATH_CELL, PRECOMPILED_XPATH_ROW, PRECOMPILED_XPATH_ROWS, XML_PARSER
from Modsmith.Extensions import ZipFileFixed
from Modsmith.ProjectSettings import ProjectSettings
from Modsmith.SimpleLogger import SimpleLogger as Log


# noinspection PyProtectedMember
class Patcher:
    def __init__(self, settings: ProjectSettings) -> None:
        self.settings: ProjectSettings = settings
        self.whitespace = re.compile('\s{2,}')
        self.remove_whitespace = partial(self.whitespace.sub, repl=' ')

    @staticmethod
    def _get_string_keys(elements: etree._Element) -> set:
        results: set = set()
        for element in elements:
            results.add(list(element)[0].text)
        return results

    @staticmethod
    def _merge_rows(elements: list, signatures: tuple, output_xml: etree._Element) -> None:
        element_name, element_attributes = signatures

        xpath: etree.XPathEvaluator = etree.XPathEvaluator(output_xml)

        rows: etree._Element = PRECOMPILED_XPATH_ROWS.evaluate(output_xml)[0]

        for element in elements:
            attributes_xpath: str = ' and '.join([f'@{key}="{element.get(key)}"' for key in sorted(element_attributes)])
            output_rows: list = xpath.evaluate('//%s[%s]' % (element_name, attributes_xpath))

            if output_rows:
                Log.debug('Replacing element: //%s[%s]' % (element_name, attributes_xpath), prefix='\t')

                for output_row in output_rows:
                    rows.remove(output_row)
                    rows.append(element)
            else:
                Log.debug('Merging element: //%s[%s]' % (element_name, attributes_xpath), prefix='\t')
                rows.append(element)

    def _merge_string_rows(self, elements: list, signatures: set, output_xml: etree._Element) -> None:
        for element in elements:
            cells: list = list(element)

            if cells[0].text in signatures:
                continue

            # we've already added our strings, let's clean them up
            for i in range(0, len(cells)):
                cell_text: str = cells[i].text

                if not cell_text:
                    continue

                if ' ' in cell_text:
                    cells[i].text = self.remove_whitespace(string=cell_text).strip()

            output_xml.append(element)

    @staticmethod
    def _try_clone_text_cells(rows: list, output_xml: etree._Element) -> None:
        """Clones text cell as translation cells if there are only two cells"""
        for row in rows:
            cells: list = list(row)

            if len(cells) == 2:
                original_text_clone: str = copy.deepcopy(cells[1])
                row.append(original_text_clone)

            output_xml.append(row)

    def _get_pak_by_path(self, xml_path: str) -> str:
        """
        Retrieves game PAK file name with extension from relative path.

        Raises FileNotFoundError if the relative path does not map to a file name.
        """
        relpath: str = Common.fix_slashes(os.path.relpath(xml_path, self.settings.project_path))

        for path in self.settings.packages:
            if relpath.startswith(path):
                return self.settings.packages[path]

        raise FileNotFoundError(f'Cannot find PAK file by path: {relpath}')

    def _get_signature_by_path(self, path: str) -> tuple:
        """
        Retrieves element signature from path.

        Raises ``NotImplementedError`` if path not found in signatures map.
        """
        path = Common.fix_slashes(path)

        for i, key in enumerate(self.settings.signatures):
            signature_key: str = next(iter(key))

            if not path.endswith(signature_key):
                continue

            signature: dict = self.settings.signatures[i][signature_key][0]
            return signature['element'], signature['attributes']

        raise NotImplementedError(f'Cannot find signature by path: {path}')

    def patch_data(self, xml_file_list: list) -> None:
        """
        Copies source, replaces existing rows with modified rows, and appends assumed new rows that cannot be found in source.

        Writes out XML to file in the build path.
        """

        # hold game paks in memory
        game_paks: dict = dict()

        for xml_file in xml_file_list:
            relative_xml_path: str = os.path.relpath(xml_file, self.settings.project_data_path)

            project_xml_path: str = os.path.join(self.settings.project_data_path, relative_xml_path)

            Log.info(f'Patching XML file: "{relative_xml_path}"')
            Log.debug(f'Source: "{project_xml_path}"', prefix='\t')

            pak_file_name: str = self._get_pak_by_path(project_xml_path)

            # we don't want to open the same game pak more than once
            if pak_file_name not in game_paks:
                # open game pak and store object in memory
                game_pak_path: str = os.path.join(self.settings.game_path, 'Data', pak_file_name)
                game_paks[pak_file_name] = ZipFileFixed(game_pak_path, mode='r')

            arcname: str = relative_xml_path.replace(os.path.sep, os.path.altsep)

            with game_paks[pak_file_name].open(arcname, 'r') as game_xml:
                # we can't use etree.parse() because we need to replace elements in _merge_rows()
                lines: list = game_xml.read().splitlines()

            output_xml: etree._Element = etree.fromstringlist(lines, XML_PARSER)

            # merge rows based on signature lookup
            project_xml_tree: etree._ElementTree = etree.parse(project_xml_path, XML_PARSER)

            rows: list = PRECOMPILED_XPATH_ROW.evaluate(project_xml_tree)
            if not rows:
                Log.warn(f'No rows found. Cannot merge: "{project_xml_path}"')
                continue

            signatures: tuple = self._get_signature_by_path(project_xml_path)

            self._merge_rows(rows, signatures, output_xml)

            build_xml_file_path: str = os.path.join(self.settings.build_data_path, relative_xml_path)

            tree: etree._ElementTree = etree.ElementTree(output_xml, parser=XML_PARSER)
            tree.write(build_xml_file_path, encoding='utf-8', pretty_print=True, xml_declaration=True)

        # close game paks open in memory
        for pak_file_path in game_paks:
            game_paks[pak_file_path].close()

    def patch_localization(self, xml_file_list: list) -> None:
        """
        Constructs XML in memory, seeds with modified rows, and appends unmodified source rows.

        Writes out XML to file in the build path.
        """

        project_i18n_path: str = self.settings.project_i18n_path
        build_i18n_path: str = self.settings.build_localization_path
        localization: list = self.settings.localization

        # hold game paks in memory
        game_paks: dict = dict()

        # filter out unsupported xml files - we can arbitrarily add these later but we can't patch them
        xml_file_list = [f for f in xml_file_list if os.path.basename(f) in localization]

        for xml_file in xml_file_list:
            relative_xml_path: str = os.path.relpath(xml_file, project_i18n_path)
            build_xml_path: str = os.path.join(build_i18n_path, relative_xml_path)

            parent_path, file_name = os.path.split(relative_xml_path)

            project_xml_path: str = os.path.join(project_i18n_path, relative_xml_path)

            Log.info(f'Patching XML file: "{relative_xml_path}"')
            Log.debug(f'project_xml_path="{project_xml_path}"', prefix='\t')

            project_xml_tree: etree._ElementTree = etree.parse(project_xml_path, XML_PARSER)
            rows: list = PRECOMPILED_XPATH_ROW.evaluate(project_xml_tree)

            if not rows:
                Log.warn(f'No rows found. Cannot patch: "{project_xml_path}"')
                continue

            # create output xml
            output_xml: etree._Element = etree.Element('Table')
            self._try_clone_text_cells(rows, output_xml)

            # read zipped pak xml
            pak_file_name: str = os.path.join(self.settings.game_path, 'Localization', parent_path + '.pak')

            if not os.path.exists(pak_file_name):
                Log.warn(f'Cannot find game package: "{pak_file_name}"')
                Log.warn(f'Skipped patching: "{project_xml_path}"')
                continue

            # we don't want to open the same game pak more than once
            if pak_file_name not in game_paks:
                # open game pak and store object in memory
                game_paks[pak_file_name] = ZipFileFixed(pak_file_name, mode='r')

            with game_paks[pak_file_name].open(file_name, mode='r') as game_xml:
                # we can't use etree.parse() because we need to replace elements in _merge_string_rows()
                lines: list = game_xml.read().splitlines()

            game_tree: etree._ElementTree = etree.fromstringlist(lines, XML_PARSER)
            game_rows: list = PRECOMPILED_XPATH_ROW.evaluate(game_tree)

            # create row data for comparing keys
            signatures: set = self._get_string_keys(output_xml)

            self._merge_string_rows(game_rows, signatures, output_xml)

            # sort output xml by key
            output_rows: list = PRECOMPILED_XPATH_ROW.evaluate(output_xml)
            output_xml[:] = sorted(output_rows, key=PRECOMPILED_XPATH_CELL.evaluate)

            with open(build_xml_path, mode='w', encoding='utf-8'):
                et: etree._ElementTree = etree.ElementTree(output_xml, parser=XML_PARSER)
                et.write(build_xml_path, encoding='utf-8', pretty_print=True)

        # close game paks open in memory
        for pak_file_path in game_paks:
            game_paks[pak_file_path].close()
