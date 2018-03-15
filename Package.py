# coding=utf-8

import configparser
import glob
import os
import zipfile

from Patcher import Patcher


class Package:
    def __init__(self, project_path, pak_filename, redist_filename):
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

    def generate_tbl(self, file, files):
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

        with zipfile.ZipFile(redist_pak_path, 'w', zipfile.ZIP_STORED) as zip_file:
            non_xml_files = [f for f in files if not f.endswith('.xml')]
            for file in non_xml_files:
                zip_file.write(file, file.replace(self.data_path, '') if not file.endswith('.tbl') else file.replace(self.redist_data_path, ''))
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

        patcher = Patcher(self)
        patcher.patch_i18n()

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
