import copy
import os
from decimal import Decimal

from lxml import etree

from modsmith import (PRECOMPILED_XPATH_ROW,
                      ProjectSettings,
                      SimpleLogger as Log,
                      XML_PARSER,
                      XML_PARSER_ALLOW_COMMENTS,
                      ZipFileFixed,
                      fix_slashes)


class Patcher:
    def __init__(self, settings: ProjectSettings) -> None:
        self.settings = settings
        self.sanitized_mod_name = self.settings.pak_file_name.lower().replace(' ', '_')

    def _get_game_pak_by_absolute_xml_path(self, xml_path: str) -> str:
        if os.path.isabs(xml_path):
            xml_path = os.path.relpath(xml_path, self.settings.project_path)

        xml_path = fix_slashes(xml_path)

        for path in self.settings.packages:
            if xml_path.startswith(path):
                return self.settings.packages[path]

        raise FileNotFoundError(f'Cannot find PAK file by path: {xml_path}')

    def _get_signature_by_path(self, path: str) -> tuple:
        path = fix_slashes(path)

        for i, key in enumerate(self.settings.signatures):
            signature_key: str = next(iter(key))

            if not path.endswith(signature_key):
                continue

            signature: dict = self.settings.signatures[i][signature_key][0]
            return signature['element'], signature['attributes']

        raise NotImplementedError(f'Cannot find signature by path: {path}')

    @staticmethod
    def find_row_differences(project_row: etree.Element, game_row: etree.Element) -> set:
        results = set()

        for project_key, project_value in project_row.attrib.items():
            if project_key not in game_row.attrib:
                results.add(project_key)
                continue

            if project_value != game_row.get(project_key):
                results.add(project_key)
                continue

        return results

    @staticmethod
    def find_root(element: etree.Element, tag: str) -> etree.Element:
        while element.getparent().tag != tag:
            element = element.getparent()
        return element.getparent()

    def patch_data(self, xml_file_list: list) -> None:
        game_paks = {}

        for xml_file in xml_file_list:
            project_xml_path_relative = os.path.relpath(xml_file, self.settings.project_data_path)
            project_xml_path_absolute = os.path.join(self.settings.project_data_path, project_xml_path_relative)

            element_name, element_attributes = self._get_signature_by_path(project_xml_path_absolute)

            Log.info(f'Patching XML file: "{project_xml_path_relative}"')
            Log.debug(f'Source: "{project_xml_path_absolute}"',
                      prefix='\t')

            game_pak_filename = self._get_game_pak_by_absolute_xml_path(project_xml_path_absolute)

            game_pak_arcname = project_xml_path_relative.replace(os.path.sep, os.path.altsep)

            # we don't want to open the same game pak more than once
            if game_pak_filename not in game_paks:
                # open game pak and store object in memory
                game_pak_path = os.path.join(self.settings.game_path, 'Data', game_pak_filename)
                game_paks.update({
                    game_pak_filename: ZipFileFixed(game_pak_path, 'r')})

            with game_paks[game_pak_filename].open(game_pak_arcname, 'r') as game_xml:
                game_xml_tree = etree.parse(game_xml, XML_PARSER)
                game_xpath = etree.XPathEvaluator(game_xml_tree)

            project_xml_tree = etree.parse(project_xml_path_absolute, XML_PARSER)

            project_rows: list = PRECOMPILED_XPATH_ROW(project_xml_tree)

            if len(project_rows) == 0:
                Log.warn(f'No rows found. Skipping: "{project_xml_path_absolute}"')
                continue

            project_xpath = etree.XPathEvaluator(project_xml_tree)
            column_data = {column.get('name').lower(): column.get('type').lower()
                           for column in project_xpath('//column')}

            duplicate_rows = set()

            for project_row in project_rows:
                project_row_parent = project_row.getparent()
                project_row_index = project_row_parent.index(project_row)

                element_attrs = ' and '.join([f'@{key}="{project_row.get(key)}"'
                                              for key in sorted(element_attributes)])

                matching_rows: list = game_xpath(f'//{element_name}[{element_attrs}]')

                if len(matching_rows) == 0:
                    continue

                if len(matching_rows) > 1:
                    raise Exception('Too many matching rows')

                if different_keys := self.find_row_differences(project_row, matching_rows[0]):
                    if any(column_data[key] == 'real' for key in different_keys):
                        duplicate_row = copy.deepcopy(project_row)

                        workaround_needed = False
                        for attr in (key for key in different_keys if column_data[key] == 'real'):
                            if Decimal(project_row.get(attr)) < Decimal(1.0):
                                duplicate_row.set(attr, '8772')
                                workaround_needed = True

                        if workaround_needed:
                            project_row_parent.insert(project_row_index, duplicate_row)
                            project_row_parent.insert(project_row_index, etree.Comment(' WORKAROUND '))
                else:
                    project_row_parent.remove(project_row)
                    duplicate_rows.add(True)

            if (count := len(duplicate_rows)) > 0:
                Log.warn(f'Removed {count} duplicate rows.', prefix='\t')

            build_xml_file_path = os.path.join(self.settings.build_data_path, project_xml_path_relative)

            target_folder = os.path.dirname(build_xml_file_path)
            os.makedirs(target_folder, exist_ok=True)

            output_database = self.find_root(project_rows[0], 'database')

            output_tree: etree.ElementTree = etree.ElementTree(output_database, parser=XML_PARSER_ALLOW_COMMENTS)
            output_tree.write(build_xml_file_path, encoding='utf-8', pretty_print=True, xml_declaration=True)

        # close game paks open in memory
        for pak_file_path in game_paks:
            game_paks[pak_file_path].close()

    def patch_localization(self, xml_file_list: list) -> None:
        game_paks = {}

        # filter out unsupported xml files - we can arbitrarily add these later but we can't patch them
        xml_file_list = (f for f in xml_file_list if os.path.basename(f) in self.settings.localization)

        for xml_file in xml_file_list:
            source_i18n_path_relative = os.path.relpath(xml_file, self.settings.project_i18n_path)
            target_i18n_path_absolute = os.path.join(self.settings.build_localization_path, source_i18n_path_relative)

            parent_path, file_name = os.path.split(source_i18n_path_relative)
            project_xml_path = os.path.join(self.settings.project_i18n_path, source_i18n_path_relative)

            Log.info(f'Patching XML file: "{source_i18n_path_relative}"')
            Log.debug(f'project_xml_path="{project_xml_path}"', prefix='\t')

            project_rows: list = PRECOMPILED_XPATH_ROW(etree.parse(project_xml_path, XML_PARSER))

            if len(project_rows) == 0:
                Log.warn(f'No rows found. Cannot patch: "{project_xml_path}"')
                continue

            project_table = project_rows[0].getparent()

            # read zipped pak xml
            game_pak_filename = os.path.join(self.settings.game_path, 'Localization', parent_path + '.pak')

            if not os.path.exists(game_pak_filename):
                Log.warn(f'Cannot find game package: "{game_pak_filename}"')
                Log.warn(f'Skipped patching: "{project_xml_path}"')
                continue

            # we don't want to open the same game pak more than once
            if game_pak_filename not in game_paks:
                game_paks.update({
                    game_pak_filename: ZipFileFixed(game_pak_filename)
                })

            with game_paks[game_pak_filename].open(file_name) as f:
                game_tree = etree.parse(f, XML_PARSER)
                game_xpath = etree.XPathEvaluator(game_tree)

            duplicate_rows = set()

            for project_row in project_rows:
                assert (count := len(project_row)) >= 2 and count <= 3

                if len(project_row) == 2:
                    project_key, project_source = (c.text for c in list(project_row))

                    # we allow two cells but the output requires three cells
                    project_source_cell = list(project_row)[1]
                    project_row.append(copy.deepcopy(project_source_cell))
                else:
                    project_key, project_source, _ = (c.text for c in list(project_row))

                matching_cells: list = game_xpath(f'//Row/Cell[text()="{project_key}"]')

                if len(matching_cells) == 0:
                    continue

                if len(matching_cells) > 1:
                    raise Exception('Too many matching rows in game tree')

                game_row = matching_cells[0].getparent()
                _, game_source, game_translation = (c.text for c in list(game_row))

                if any(project_source == text for text in [game_source, game_translation]):
                    project_table.remove(project_row)
                    duplicate_rows.add(project_key)

            if (count := len(duplicate_rows)) > 0:
                Log.warn(f'Removed {count} duplicate rows.', prefix='\t')

            output_root = self.find_root(project_rows[0], 'Table')

            with open(target_i18n_path_absolute, 'w', encoding='utf-8'):
                output_tree = etree.ElementTree(output_root, parser=XML_PARSER_ALLOW_COMMENTS)
                output_tree.write(target_i18n_path_absolute, encoding='utf-8', pretty_print=True)

        # close game paks open in memory
        for pak_file_path in game_paks:
            game_paks[pak_file_path].close()
