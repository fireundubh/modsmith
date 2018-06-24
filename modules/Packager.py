import glob
import os
import operator
import zipfile

from functools import reduce

from modules.Database import EXCLUSIONS
from modules.Package import Package
from modules.Patcher import Patcher


class Packager(Package):
    def __init__(self, project_path, project_i18n_path, output_pak_file_name, redist_file_name, cfg_path):
        self.settings = [project_path, project_i18n_path, output_pak_file_name, redist_file_name, cfg_path]
        self.sep = '-' * 80
        super(Packager, self).__init__(*self.settings)

    # PRIVATE METHODS
    def _generate_tbl_files(self, files: list) -> list:
        """
        Generate empty files with the .tbl extension

        :param files: List of files to be used to generate the PAK
        :return: List of TBL files created
        """
        results = []

        tbl_files = [f.replace('.xml', '.tbl').replace(self.project_data_path, self.redist_data_path) for f in files if 'Data\Libs\Tables' in f]

        for tbl_file in tbl_files:
            os.makedirs(os.path.dirname(tbl_file), exist_ok=True)
            open(tbl_file, 'w').close()
            results.append(tbl_file)

        return results

    def _prepare_i18n_targets(self, folders: list) -> list:
        """
        Generates a list i18n XML files, and creates output directories if needed
        :param folders: List of folders containing i18n data
        :return: list of files with full paths
        """
        xml_files = list()

        for folder in folders:
            files = glob.glob(os.path.join(self.project_i18n_path, folder, '*.xml'), recursive=False)
            if files is not None and len(files) > 0:
                os.makedirs(os.path.join(self.redist_i18n_path, folder), exist_ok=True)
                xml_files.extend(files)

        return xml_files

    # PUBLIC METHODS
    def generate_pak(self):
        os.makedirs(self.redist_data_path, exist_ok=True)

        all_files = [f for f in glob.glob(os.path.join(self.project_data_path, '**\*'), recursive=True) if os.path.isfile(f) and not f.endswith('.pak')]

        # we only care about xml files for patching and tbl generation
        xml_files = [f for f in all_files if f.endswith('.xml')]

        # separate support and unsupported files
        xml_files_supported = set([f for f in xml_files if not any(x in f for x in EXCLUSIONS)])
        xml_files_unsupported = set(xml_files) - set(xml_files_supported)

        # generate tbl files and merge them with files to be packaged
        all_files += self._generate_tbl_files(xml_files)

        # separate non-xml files from xml files
        other_files = set(all_files) - set(xml_files)

        patcher = Patcher(*self.settings)
        patcher.patch_data(xml_files_supported)

        print(f'\nWriting PAK:\t{self.redist_pak_path}\n{self.sep}')

        with zipfile.ZipFile(self.redist_pak_path, 'w', zipfile.ZIP_STORED) as zip_file:
            output_files = self.assemble_file_list(xml_files_supported, xml_files_unsupported, other_files)

            for file, arc_name in output_files:
                zip_file.write(file, arc_name)

                print(f'Packaged file:\t{file} (as {arc_name})')

    def generate_i18n(self):
        folder_names = os.listdir(self.project_i18n_path)

        xml_files = self._prepare_i18n_targets(folder_names)
        reduce(operator.concat, xml_files)

        patcher = Patcher(*self.settings)
        patcher.patch_i18n(xml_files)

        for folder_name in folder_names:
            redist_folder_path = os.path.join(self.redist_i18n_path, folder_name)
            pak_file_name = redist_folder_path + self.output_pak_extension

            print(f'\nWriting PAK:\t{pak_file_name}\n{self.sep}')

            with zipfile.ZipFile(pak_file_name, mode='w', compression=zipfile.ZIP_STORED) as zip_file:
                for file in glob.glob(os.path.join(redist_folder_path, '*.xml'), recursive=False):
                    arc_name = os.path.relpath(file, redist_folder_path)
                    zip_file.write(file, arc_name)

                    print(f'Packaged file:\t{file} (as {arc_name})')

    def pack(self):
        zip_archive = os.path.join(self.redist_path, self.redist_file_name)

        print(f'\nWriting ZIP:\t{zip_archive}\n{self.sep}')

        with zipfile.ZipFile(zip_archive, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(*self.manifest)

            print(f'Packaged file:\t{self.manifest_path} (as {self.manifest_arc_name})')

            files = glob.glob(os.path.join(self.redist_path, self.redist_name, '**\*.pak'), recursive=True)
            other_files = [f for f in glob.glob(os.path.join(self.project_path, '**\*.pak'), recursive=True) if
                           self.redist_path not in os.path.dirname(f)]

            for file in files + other_files:
                if file in other_files:
                    arc_name = os.path.join(self.redist_name, os.path.relpath(file, self.project_path))
                else:
                    arc_name = os.path.relpath(file, self.redist_path)

                zip_file.write(file, arc_name)

                print(f'Packaged file:\t{file} (as {arc_name})')
