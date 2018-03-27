# coding=utf-8

import configparser
import glob
import os
import zipfile

from modules.Database import EXCLUSIONS
from modules.Patcher import Patcher


class Packager:
    def __init__(self, project_path, i18n_project_path, pak_filename, redist_filename, cfg_path):
        """
        Sets up the necessary paths for building PAKs

        :param project_path: Path to the Modsmith project root
        :param pak_filename: File name with extension for the output PAK
        :param redist_filename: File name with extension for the output ZIP
        """
        if not project_path:
            raise ValueError('Cannot pass None for project_path')

        if not pak_filename:
            raise ValueError('Cannot pass None for pak_filename')

        if not redist_filename:
            raise ValueError('Cannot pass None for redist_filename')

        self.project_path = project_path
        self.data_path = os.path.join(self.project_path, 'Data')
        self.data_filename = pak_filename

        self.redist_filename = redist_filename
        self.redist_name = os.path.splitext(self.redist_filename)[0]
        self.redist_path = os.path.join(self.project_path, 'Build')
        self.redist_data_path = os.path.join(self.redist_path, self.redist_name, 'Data')
        self.redist_pak_path = os.path.join(self.redist_data_path, self.data_filename)

        if not i18n_project_path:
            self.i18n_project_path = os.path.join(self.project_path, 'Localization')
        else:
            self.i18n_project_path = i18n_project_path

        self.i18n_redist_path = os.path.join(self.redist_path, self.redist_name, 'Localization')
        self.manifest_path = os.path.join(self.project_path, 'mod.manifest')
        self.manifest_arcname = os.path.join(self.redist_name, 'mod.manifest')
        self.manifest = [self.manifest_path, self.manifest_arcname]

        self.config = configparser.ConfigParser()

        if not cfg_path:
            self.config.read('modsmith.conf')
        else:
            self.config.read(cfg_path)

    # TODO: generate real tbl files
    def generate_tbl_files(self, files):
        """
        Generate empty files with the .tbl extension

        :param files: List of files to be used to generate the PAK
        :return: List of TBL files created
        """
        results = []

        for file in files:
            tbl_file = file.replace('.xml', '.tbl').replace(self.data_path, self.redist_data_path)

            os.makedirs(os.path.dirname(tbl_file), exist_ok=True)
            open(tbl_file, 'w').close()

            results.append(tbl_file)

        return results

    def assemble_file_list(self, supported_xml_files, unsupported_xml_files, non_xml_files):
        """
        Assembles multiple lists into a single list of files to be packaged

        :param supported_xml_files: List of patchable XML files to be packaged
        :param unsupported_xml_files: List of unpatchable XML files to be packaged
        :param non_xml_files: List of non-XML files to be packaged
        :return: List of files to be packaged
        """
        results = []

        for file in supported_xml_files:
            target_file = os.path.join(self.redist_data_path, os.path.relpath(file, self.data_path))
            arcname = os.path.relpath(file, self.data_path)
            results.append((target_file, arcname))

        for file in unsupported_xml_files:
            arcname = os.path.relpath(file, self.data_path)
            results.append((file, arcname))

        for file in non_xml_files:
            arcname = os.path.relpath(file, self.redist_data_path) if file.endswith('.tbl') else os.path.relpath(file, self.data_path)
            results.append((file, arcname))

        return results

    def generate_pak(self):
        os.makedirs(self.redist_data_path, exist_ok=True)

        files = [f for f in glob.glob(os.path.join(self.data_path, '**\*'), recursive=True) if os.path.isfile(f)]

        # we only care about xml files for patching and tbl generation
        xml_files = [f for f in files if f.endswith('xml')]

        # generate tbl files and merge them with files to be packaged
        files += self.generate_tbl_files(xml_files)

        Patcher(self).patch_data(xml_files)

        print('\nWriting PAK:\t%s\n%s' % (self.redist_pak_path, '-' * 80))

        with zipfile.ZipFile(self.redist_pak_path, 'w', zipfile.ZIP_STORED) as zip_file:
            supported_xml_files = [f for f in xml_files if not any(x in f for x in EXCLUSIONS)]
            unsupported_xml_files = set(xml_files) - set(supported_xml_files)
            non_xml_files = set(files) - set(xml_files)

            # assemble list of files to be packaged
            output_files = self.assemble_file_list(supported_xml_files, unsupported_xml_files, non_xml_files)

            # write list of files to package
            for file, arcname in sorted(output_files):
                zip_file.write(file, arcname)

                print('Packaged file:\t%s (as %s)' % (file, arcname))

    def generate_i18n_file_list(self, folders):
        """
        Creates a list of i18n files

        :param folders: List of folder names
        :return: List of i18n files
        """
        results = []

        for folder in folders:
            os.makedirs(os.path.join(self.i18n_redist_path, folder), exist_ok=True)
            results += glob.glob(os.path.join(self.i18n_project_path, folder, '*.xml'), recursive=False)

        return results

    def generate_i18n(self):
        folder_names = os.listdir(self.i18n_project_path)

        xml_files = self.generate_i18n_file_list(folder_names)

        Patcher(self).patch_i18n(xml_files)

        for folder_name in folder_names:
            redist_folder_path = os.path.join(self.i18n_redist_path, folder_name)
            pak_filename = redist_folder_path + '.pak'

            print('\nWriting PAK:\t%s\n%s' % (pak_filename, '-' * 80))

            with zipfile.ZipFile(pak_filename, 'w', compression=zipfile.ZIP_STORED) as zip_file:
                files = glob.glob(os.path.join(redist_folder_path, '*.xml'), recursive=False)

                for file in sorted(files):
                    arcname = os.path.relpath(file, os.path.join(self.i18n_redist_path, folder_name))
                    zip_file.write(file, arcname)

                    print('Packaged file:\t%s (as %s)' % (file, arcname))

    def pack(self):
        zip_archive = os.path.join(self.redist_path, self.redist_filename)

        print('\nWriting ZIP:\t%s\n%s' % (zip_archive, '-' * 80))

        with zipfile.ZipFile(zip_archive, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(*self.manifest)
            print('Packaged file:\t%s (as %s)' % (self.manifest_path, self.manifest_arcname))

            files = glob.glob(os.path.join(self.redist_path, self.redist_name, '**\*.pak'), recursive=True)

            for file in files:
                arcname = os.path.relpath(file, self.redist_path)
                zip_file.write(file, arcname)

                print('Packaged file:\t%s (as %s)' % (file, arcname))
