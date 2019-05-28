import fnmatch
import glob
import operator
import os
from functools import reduce
from shutil import copy2
from zipfile import ZIP_DEFLATED, ZIP_STORED

from modules.Database import Database
from modules.Package import Package
from modules.Patcher import Patcher
from modules.SimpleLogger import SimpleLogger as Log

from stdlib.zipfilePatch import ZipFileFixed


class Packager(Package):
    def __init__(self, project_path, project_i18n_path, output_pak_file_name, redist_file_name, cfg_path, allow_arbitrary_files):
        self.allow_arbitrary_files = allow_arbitrary_files
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
        xml_files_supported = set([f for f in xml_files if not any(x.lower() in f.lower() for x in Database.get_exclusions())])
        xml_files_unsupported = set(xml_files) - set(xml_files_supported)

        # generate tbl files and merge them with files to be packaged
        all_files += self._generate_tbl_files(xml_files)

        # separate non-xml files from xml files
        other_files = set(all_files) - set(xml_files)

        Log.info('Patching supported game data...%s%s' % (os.linesep, self.sep), os.linesep)
        patcher = Patcher(*self.settings)
        patcher.patch_data(xml_files_supported)

        Log.info('Writing PAK:\t%s%s%s' % (self.redist_pak_path, os.linesep, self.sep), os.linesep)

        with ZipFileFixed(self.redist_pak_path, 'w', ZIP_STORED) as zip_file:
            output_files = self.assemble_file_list(xml_files_supported, xml_files_unsupported, other_files)

            for file, arc_name in output_files:
                zip_file.write(file, arc_name)

                Log.info('File added to PAK:\t%s (as %s)' % (file, arc_name))

    def generate_i18n(self):
        folder_names = os.listdir(self.project_i18n_path)

        xml_files = self._prepare_i18n_targets(folder_names)
        try:
            reduce(operator.concat, xml_files)
        except TypeError:
            Log.error('Failed to prepare i18n targets.')
            if len(folder_names) > 0:
                Log.info('Is your folder structure correct? (e.g., Localization\english_xml\*.xml)', '\t', os.linesep)
            raise

        Log.info('Patching supported localization...%s%s' % (os.linesep, self.sep), os.linesep)
        patcher = Patcher(*self.settings)
        patcher.patch_i18n(xml_files)

        for folder_name in folder_names:
            redist_folder_path = os.path.join(self.redist_i18n_path, folder_name)

            if not os.path.exists(redist_folder_path):
                Log.warn('Cannot write PAK. Folder missing:\t%s' % redist_folder_path, os.linesep)
                continue

            if len(fnmatch.filter(os.listdir(redist_folder_path), '*.xml')) == 0:
                Log.warn('Cannot write PAK. Folder does not contain XML files:\t%s' % redist_folder_path, os.linesep)
                continue

            pak_file_name = redist_folder_path + self.output_pak_extension

            Log.info('Writing PAK:\t%s%s%s' % (pak_file_name, os.linesep, self.sep), os.linesep)

            with ZipFileFixed(pak_file_name, mode='w', compression=ZIP_STORED) as zip_file:
                if self.allow_arbitrary_files:
                    for f in xml_files:
                        _, file_name = os.path.split(f)

                        supported_xml_files = Database.get_localization()

                        if file_name not in supported_xml_files:
                            output_path = os.path.join(redist_folder_path, file_name)
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            copy2(f, output_path)

                            Log.info('File copied for PAK:\t%s (as %s)' % (f, output_path))

                for f in glob.glob(os.path.join(redist_folder_path, '*.xml'), recursive=False):
                    arc_name = os.path.relpath(f, redist_folder_path)
                    zip_file.write(f, arc_name)

                    Log.info('File added to PAK:\t%s (as %s)' % (f, arc_name))

    def pack(self):
        zip_archive = os.path.join(self.redist_path, self.redist_file_name)

        Log.info('Writing ZIP:\t%s%s%s' % (zip_archive, os.linesep, self.sep), os.linesep)

        with ZipFileFixed(zip_archive, mode='w', compression=ZIP_DEFLATED) as zip_file:
            zip_file.write(*self.manifest)

            Log.info('File added to ZIP:\t%s (as %s)' % (self.manifest_path, self.manifest_arc_name))

            files = glob.glob(os.path.join(self.redist_path, self.redist_name, '**\*.pak'), recursive=True)
            other_files = [f for f in glob.glob(os.path.join(self.project_path, '**\*.pak'), recursive=True) if
                           self.redist_path not in os.path.dirname(f)]

            for file in files + other_files:
                if file in other_files:
                    arc_name = os.path.join(self.redist_name, os.path.relpath(file, self.project_path))
                else:
                    arc_name = os.path.relpath(file, self.redist_path)

                zip_file.write(file, arc_name)

                Log.info('File added to ZIP:\t%s (as %s)' % (file, arc_name))
