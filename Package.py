# coding=utf-8

import configparser
import glob
import os
import zipfile

from Database import EXCLUSIONS
from Patcher import Patcher


class Package:
    def __init__(self, project_path, pak_filename, redist_filename):
        """
        Sets up the necessary paths for building PAKs

        :param project_path: Path to the Modsmith project root
        :param pak_filename: File name with extension for the output PAK
        :param redist_filename: File name with extension for the output ZIP
        """

        self.project_path = project_path
        self.data_path = os.path.join(self.project_path, 'Data')
        self.data_filename = pak_filename
        self.data_xml_files = []
        self.redist_filename = redist_filename
        self.redist_name = os.path.splitext(self.redist_filename)[0]
        self.redist_path = os.path.join(self.project_path, 'Build')
        self.redist_data_path = os.path.join(self.redist_path, self.redist_name, 'Data')
        self.i18n_project_path = os.path.join(self.project_path, 'Localization')
        self.i18n_redist_path = os.path.join(self.redist_path, self.redist_name, 'Localization')
        self.i18n_xml_files = []
        self.manifest_path = os.path.join(self.project_path, 'mod.manifest')
        self.manifest_arcname = os.path.join(self.redist_name, 'mod.manifest')
        self.manifest = [self.manifest_path, self.manifest_arcname]
        self.config = configparser.ConfigParser()
        self.config.read('modsmith.conf')

    # TODO: generate real tbl files
    def generate_tbl(self, file, files):
        """
        Generate empty files with the .tbl extension

        :param file: XML file whose name should be used for the empty file
        :param files: List of files to be used to generate the PAK
        :return: None
        """
        # try to create zero-byte .tbl files
        tbl_file = file.replace('.xml', '.tbl').replace(self.data_path, self.redist_data_path)

        if tbl_file not in files:
            if not os.path.exists(tbl_file):
                os.makedirs(os.path.dirname(tbl_file), exist_ok=True)
                open(tbl_file, 'w').close()

            files.append(tbl_file)

    def generate_pak(self):
        os.makedirs(self.redist_data_path, exist_ok=True)

        files = [f for f in glob.glob(os.path.join(self.data_path, '**\*'), recursive=True) if os.path.isfile(f)]

        for file in files:
            if not file.endswith('.xml'):
                continue

            self.generate_tbl(file, files)
            self.data_xml_files.append(file)

        patcher = Patcher(self)
        patcher.patch_data()

        redist_pak_path = os.path.join(self.redist_data_path, self.data_filename)

        print('\nWriting PAK:\t%s' % redist_pak_path)
        print('-' * 80)

        with zipfile.ZipFile(redist_pak_path, 'w', zipfile.ZIP_STORED) as zip_file:
            non_xml_files = [f for f in files if not f.endswith('.xml')]
            supported_xml_files = [f for f in self.data_xml_files if not any(x in f for x in EXCLUSIONS)]
            unsupported_xml_files = [f for f in self.data_xml_files if any(x in f for x in EXCLUSIONS)]

            output_files = []

            for file in non_xml_files:
                if file.endswith('.tbl'):
                    arcname = os.path.relpath(file, self.redist_data_path)
                else:
                    arcname = os.path.relpath(file, self.data_path)
                output_files.append((file, arcname))

            for file in supported_xml_files:
                target_file = os.path.join(self.redist_data_path, os.path.relpath(file, self.data_path))
                arcname = os.path.relpath(file, self.data_path)
                output_files.append((target_file, arcname))

            for file in unsupported_xml_files:
                arcname = os.path.relpath(file, self.data_path)
                output_files.append((file, arcname))

            for file, arcname in sorted(output_files):
                zip_file.write(file, arcname)
                print('Packaged file:\t%s (as %s)' % (file, arcname))

    def generate_i18n(self):
        language_paths = os.listdir(self.i18n_project_path)

        for lang in language_paths:
            lang_path = os.path.join(self.i18n_redist_path, lang)
            os.makedirs(lang_path, exist_ok=True)

            files = glob.glob(os.path.join(self.i18n_project_path, lang, '*.xml'), recursive=False)

            for file in files:
                self.i18n_xml_files.append(file)

        patcher = Patcher(self)
        patcher.patch_i18n()

        for lang in language_paths:
            lang_path = os.path.join(self.i18n_redist_path, lang)

            print('\nWriting PAK:\t%s' % lang_path + '.pak')
            print('-' * 80)

            with zipfile.ZipFile(lang_path + '.pak', 'w', compression=zipfile.ZIP_STORED) as zip_file:
                files = glob.glob(os.path.join(lang_path, '*.xml'), recursive=False)

                for file in files:
                    arcname = os.path.relpath(file, os.path.join(self.i18n_redist_path, lang))
                    zip_file.write(file, arcname)

                    print('Packaged file:\t%s (as %s)' % (file, arcname))

    def pack(self):
        zip_archive = os.path.join(self.redist_path, self.redist_filename)

        print('\nWriting ZIP:\t%s' % zip_archive)
        print('-' * 80)

        with zipfile.ZipFile(zip_archive, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(*self.manifest)
            print('Packaged file:\t%s (as %s)' % (self.manifest_path, self.manifest_arcname))

            files = glob.glob(os.path.join(self.redist_path, self.redist_name, '**\*.pak'), recursive=True)

            for file in files:
                arcname = os.path.relpath(file, self.redist_path)
                zip_file.write(file, arcname)

                print('Packaged file:\t%s (as %s)' % (file, arcname))
