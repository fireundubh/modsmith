import fnmatch
import glob
import operator
import os
import shutil
from functools import reduce
from typing import Generator
from zipfile import ZIP_DEFLATED, ZIP_STORED

from Modsmith.Extensions import ZipFileFixed
from Modsmith.Patcher import Patcher
from Modsmith.ProjectOptions import ProjectOptions
from Modsmith.ProjectSettings import ProjectSettings
from Modsmith.SimpleLogger import SimpleLogger as Log


class Packager:
    def __init__(self, settings: ProjectSettings) -> None:
        self.settings: ProjectSettings = settings
        self.options: ProjectOptions = settings.options
        self.sep = '-' * 80

        self.glob_all_files = os.path.join(self.settings.project_data_path, '**\*')
        self.glob_project_paks: str = os.path.join(self.settings.project_path, '**\*.pak')
        self.glob_build_paks: str = os.path.join(self.settings.build_zip_folder_path, '**\*.pak')

    @staticmethod
    def _copy_assets_to_build_path(xml_files: list, build_lang_path: str, excluded_files: list) -> None:
        for filename in xml_files:
            file_name: str = os.path.basename(filename)

            if file_name in excluded_files:
                continue

            # TODO: check if we need to dirname
            output_file_path: str = os.path.join(build_lang_path, file_name)

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            shutil.copy2(filename, output_file_path)

            Log.info(f'File copied for PAK: "{filename}"')
            Log.debug(f'output_file_path="{output_file_path}"', prefix='\t')

    def _generate_tbl_files(self, files: list) -> list:
        """Generate empty files with the .tbl extension"""

        project_data_path: str = self.settings.project_data_path
        build_data_path: str = self.settings.build_data_path

        tbl_files: list = [f.replace('.xml', '.tbl').replace(project_data_path, build_data_path)
                           for f in files if 'Data\Libs\Tables'.lower() in f.lower()]

        results: list = []

        for tbl_file in tbl_files:
            tbl_folder: str = os.path.dirname(tbl_file)
            if not os.path.exists(tbl_folder):
                os.makedirs(tbl_folder)
            if not os.path.exists(tbl_file):
                open(tbl_file, 'w').close()
            results.append(tbl_file)

        return results

    def _prepare_i18n_targets(self, folders: list) -> list:
        """Generates a list i18n XML files, and creates output directories if needed"""

        project_i18n_path: str = self.settings.project_i18n_path
        build_localization_path: str = self.settings.build_localization_path

        xml_files: list = []

        for folder in folders:
            files: list = glob.glob(os.path.join(project_i18n_path, folder, '*.xml'), recursive=False)

            if files:
                os.makedirs(os.path.join(build_localization_path, folder), exist_ok=True)
                xml_files.extend(files)

        return xml_files

    def _generate_file_list(self, supported_xml_files: set, unsupported_xml_files: set, non_xml_files: set) -> Generator:
        project_data_path: str = self.settings.project_data_path
        build_data_path: str = self.settings.build_data_path

        for supported_file in supported_xml_files:
            arcname: str = os.path.relpath(supported_file, project_data_path)
            target_file: str = os.path.join(build_data_path, arcname)
            yield target_file, arcname

        for unsupported_file in unsupported_xml_files.union(non_xml_files):
            data_path: str = build_data_path if unsupported_file.endswith('.tbl') else project_data_path
            target_arcname = os.path.relpath(unsupported_file, data_path)
            yield unsupported_file, target_arcname

    def generate_pak(self) -> None:
        build_package_path: str = self.settings.build_package_path
        exclusions: list = self.settings.exclusions

        make_project_relative = self.settings.make_project_relative

        all_files: list = [f for f in glob.glob(self.glob_all_files, recursive=True) if os.path.isfile(f) and not f.endswith('.pak')]

        # we only care about xml files for patching and tbl generation
        xml_files: list = [f for f in all_files if f.endswith('.xml')]

        # separate supported and unsupported files
        xml_files_supported: set = set([f for f in xml_files if not any(x.lower() in f.lower() for x in exclusions)])

        xml_files_unsupported: set = set(xml_files) - set(xml_files_supported)

        # generate tbl files and merge them with files to be packaged
        all_files += self._generate_tbl_files(xml_files)

        # separate non-xml files from xml files
        other_files: set = set(all_files) - set(xml_files)

        Log.info('Patching game data...',
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        patcher: Patcher = Patcher(self.settings)
        patcher.patch_data(list(xml_files_supported))

        Log.info('Writing PAK: "%s"' % make_project_relative(build_package_path),
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        os.makedirs(os.path.dirname(build_package_path), exist_ok=True)

        with ZipFileFixed(build_package_path, 'w', ZIP_STORED) as zip_file:
            for filename, arcname in self._generate_file_list(xml_files_supported, xml_files_unsupported, other_files):
                zip_file.write(filename, arcname)

                Log.info('File added to PAK: "%s"' % make_project_relative(filename))
                Log.debug(f'arcname="{arcname}"', prefix='\t')

    def generate_i18n(self) -> None:
        project_i18n_path: str = self.settings.project_i18n_path
        build_localization_path: str = self.settings.build_localization_path
        pak_extension: str = self.settings.pak_extension
        localization: list = self.settings.localization

        make_project_relative = self.settings.make_project_relative

        folder_names: list = os.listdir(project_i18n_path)
        xml_files: list = self._prepare_i18n_targets(folder_names)

        try:
            reduce(operator.concat, xml_files)
        except TypeError:
            Log.error('Failed to prepare i18n targets.')
            if folder_names:
                Log.info('Is your folder structure correct? (e.g., Localization\english_xml\*.xml)',
                         prefix='\t', suffix=os.linesep)
            raise

        Log.info('Patching localization...',
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        patcher: Patcher = Patcher(self.settings)
        patcher.patch_localization(xml_files)

        for folder_name in folder_names:
            build_lang_path: str = os.path.join(build_localization_path, folder_name)
            glob_build_lang_xml: str = os.path.join(build_lang_path, '*.xml')

            if not os.path.exists(build_lang_path):
                Log.warn(f'Cannot build PAK. Folder missing: "{build_lang_path}"',
                         prefix=os.linesep)
                continue

            if len(fnmatch.filter(os.listdir(build_lang_path), '*.xml')) == 0:
                Log.warn(f'Cannot build PAK. Folder empty or does not contain XML files: "{build_lang_path}"',
                         prefix=os.linesep)
                continue

            lang_pak_file_name: str = build_lang_path + pak_extension

            Log.info('Writing PAK: "%s"' % make_project_relative(lang_pak_file_name),
                     prefix=os.linesep, suffix=os.linesep + self.sep)

            if self.options.pack_assets:
                self._copy_assets_to_build_path(xml_files, build_lang_path, localization)

            os.makedirs(os.path.dirname(lang_pak_file_name), exist_ok=True)

            with ZipFileFixed(lang_pak_file_name, mode='w', compression=ZIP_STORED) as zip_file:
                for filename in glob.glob(glob_build_lang_xml, recursive=False):
                    arcname: str = os.path.relpath(filename, build_lang_path)
                    zip_file.write(filename, arcname)

                    Log.info('File added to PAK: "%s"' % make_project_relative(filename))
                    Log.debug(f'arcname="{arcname}"', prefix='\t')

    def pack(self) -> str:
        """Writes build assets to ZIP file. Returns output ZIP file path."""

        project_manifest_path: str = self.settings.project_manifest_path
        project_build_path: str = self.settings.project_build_path
        build_zip_file_path: str = self.settings.build_zip_file_path
        pak_name: str = self.settings.pak_file_name
        zip_manifest_arc_name: str = self.settings.zip_manifest_arc_name

        make_project_relative = self.settings.make_project_relative

        Log.info('Writing ZIP: "%s"' % make_project_relative(build_zip_file_path),
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        os.makedirs(os.path.dirname(build_zip_file_path), exist_ok=True)

        with ZipFileFixed(build_zip_file_path, mode='w', compression=ZIP_DEFLATED) as zip_file:
            zip_file.write(project_manifest_path, zip_manifest_arc_name, compress_type=ZIP_DEFLATED)

            Log.info('File added to ZIP: "%s"' % make_project_relative(project_manifest_path))
            Log.debug(f'arcname="{zip_manifest_arc_name}"', prefix='\t')

            build_pak_files: list = glob.glob(self.glob_build_paks, recursive=True)

            project_pak_files: list = [f for f in glob.glob(self.glob_project_paks, recursive=True) if
                                       project_build_path not in os.path.dirname(f)]

            for filename in build_pak_files + project_pak_files:
                if filename in project_pak_files:
                    arcname: str = os.path.join(pak_name, make_project_relative(filename))
                else:
                    arcname = os.path.relpath(filename, project_build_path)

                zip_file.write(filename, arcname)

                Log.info('File added to ZIP: "%s"' % make_project_relative(filename))
                Log.debug(f'arcname="{arcname}"', prefix='\t')

        return build_zip_file_path
