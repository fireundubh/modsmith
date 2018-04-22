# coding=utf-8

import configparser
import os
import types


class Package:
    def __init__(self, project_path, project_i18n_path, output_pak_file_name, redist_file_name, cfg_path):
        """
        Sets up the necessary paths for building PAKs

        :param project_path: Path to the Modsmith project root
        :param output_pak_file_name: File name with extension for the output PAK
        :param redist_file_name: File name with extension for the output ZIP
        """
        self.project_path = project_path
        self.project_data_path = os.path.join(self.project_path, 'Data')
        self.output_pak_name, self.output_pak_extension = os.path.splitext(output_pak_file_name)

        self.redist_file_name = redist_file_name
        self.redist_name, self.redist_extension = os.path.splitext(redist_file_name)
        self.redist_path = os.path.join(self.project_path, 'Build')
        self.redist_data_path = os.path.join(self.redist_path, self.redist_name, 'Data')
        self.redist_pak_path = os.path.join(self.redist_data_path, self.output_pak_name)

        if not project_i18n_path:
            self.project_i18n_path = os.path.join(self.project_path, 'Localization')
        else:
            self.project_i18n_path = project_i18n_path

        self.redist_i18n_path = os.path.join(self.redist_path, self.redist_name, 'Localization')
        self.manifest_path = os.path.join(self.project_path, 'mod.manifest')
        self.manifest_arc_name = os.path.join(self.redist_name, 'mod.manifest')
        self.manifest = [self.manifest_path, self.manifest_arc_name]

        self.config = configparser.ConfigParser()

        self.cfg_path = cfg_path

        if not cfg_path:
            self.config.read('modsmith.conf')
        else:
            self.config.read(cfg_path)

    def assemble_file_list(self, supported_xml_files: set, unsupported_xml_files: set, non_xml_files: set) -> types.GeneratorType:
        for file in supported_xml_files:
            arc_name = os.path.relpath(file, self.project_data_path)
            target_file = os.path.join(self.redist_data_path, arc_name)
            yield target_file, arc_name

        for file in unsupported_xml_files.union(non_xml_files):
            if file.endswith('.tbl'):
                arc_name = os.path.relpath(file, self.redist_data_path)
            else:
                arc_name = os.path.relpath(file, self.project_data_path)
            yield file, arc_name
