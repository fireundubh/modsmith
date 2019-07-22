import fnmatch
import glob
import operator
import os
import shutil
from functools import reduce
from typing import Generator
from zipfile import ZIP_DEFLATED, ZIP_STORED

from contracts import contract, disable_all

from Modsmith.Constants import PRODUCTION
from Modsmith.Extensions import ZipFileFixed
from Modsmith.Patcher import Patcher
from Modsmith.ProjectOptions import ProjectOptions
from Modsmith.ProjectSettings import ProjectSettings
from Modsmith.SimpleLogger import SimpleLogger as Log

if PRODUCTION:
    disable_all()


class Packager:
    def __init__(self, settings: ProjectSettings) -> None:
        self.settings: ProjectSettings = settings
        self.options: ProjectOptions = settings.options
        self.sep = '-' * 80

    @contract(files=list)
    def _generate_tbl_files(self, files: list) -> list:
        """Generate empty files with the .tbl extension"""
        results: list = []

        tbl_files: list = [f.replace('.xml', '.tbl').replace(self.settings.project_data_path, self.settings.build_data_path)
                           for f in files if 'Data\Libs\Tables' in f]

        for tbl_file in tbl_files:
            os.makedirs(os.path.dirname(tbl_file), exist_ok=True)
            open(tbl_file, 'w').close()
            results.append(tbl_file)

        return results

    @contract(folders=list)
    def _prepare_i18n_targets(self, folders: list) -> list:
        """Generates a list i18n XML files, and creates output directories if needed"""
        xml_files: list = []

        for folder in folders:
            files: list = glob.glob(os.path.join(self.settings.project_localization_path, folder, '*.xml'), recursive=False)

            if not files:
                continue

            os.makedirs(os.path.join(self.settings.build_localization_path, folder), exist_ok=True)

            xml_files.extend(files)

        return xml_files

    @contract(supported_xml_files=set, unsupported_xml_files=set, non_xml_files=set)
    def _assemble_file_list(self, supported_xml_files: set, unsupported_xml_files: set, non_xml_files: set) -> Generator:
        for supported_file in supported_xml_files:
            arc_name: str = os.path.relpath(supported_file, self.settings.project_data_path)
            target_file: str = os.path.join(self.settings.build_data_path, arc_name)
            yield target_file, arc_name

        for unsupported_file in unsupported_xml_files.union(non_xml_files):
            data_path: str = self.settings.build_data_path if unsupported_file.endswith('.tbl') else self.settings.project_data_path
            target_arc_name = os.path.relpath(unsupported_file, data_path)
            yield unsupported_file, target_arc_name

    def generate_pak(self) -> None:
        os.makedirs(self.settings.build_data_path, exist_ok=True)

        all_files: list = [f for f in glob.glob(os.path.join(self.settings.project_data_path, '**\*'), recursive=True)
                           if os.path.isfile(f) and not f.endswith('.pak')]

        # we only care about xml files for patching and tbl generation
        xml_files: list = [f for f in all_files if f.endswith('.xml')]

        # separate support and unsupported files
        xml_files_supported: set = set([xml_file for xml_file in xml_files
                                        if not any(x.lower() in xml_file.lower() for x in self.settings.exclusions)])

        xml_files_unsupported: set = set(xml_files) - set(xml_files_supported)

        # generate tbl files and merge them with files to be packaged
        all_files += self._generate_tbl_files(xml_files)

        # separate non-xml files from xml files
        other_files: set = set(all_files) - set(xml_files)

        Log.info('Patching game data...',
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        patcher: Patcher = Patcher(self.settings)
        patcher.patch_data(list(xml_files_supported))

        Log.info(f'Writing PAK: "{self.options.relpath(self.settings.build_package_path)}"',
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        with ZipFileFixed(self.settings.build_package_path, 'w', ZIP_STORED) as zip_file:
            for filename, arcname in self._assemble_file_list(xml_files_supported, xml_files_unsupported, other_files):
                zip_file.write(filename, arcname)

                Log.info(f'File added to PAK: "{self.options.relpath(filename)}"')
                Log.debug(f'arcname="{arcname}"', prefix='\t')

    def generate_i18n(self) -> None:
        folder_names: list = os.listdir(self.settings.project_localization_path)

        xml_files: list = self._prepare_i18n_targets(folder_names)

        try:
            reduce(operator.concat, xml_files)
        except TypeError:
            Log.error('Failed to prepare i18n targets.')
            if len(folder_names) > 0:
                Log.info('Is your folder structure correct? (e.g., Localization\english_xml\*.xml)',
                         prefix='\t', suffix=os.linesep)
            raise

        Log.info('Patching localization...',
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        patcher: Patcher = Patcher(self.settings)
        patcher.patch_localization(xml_files)

        for folder_name in folder_names:
            build_lang_path: str = os.path.join(self.settings.build_localization_path, folder_name)

            if not os.path.exists(build_lang_path):
                Log.warn(f'Cannot build PAK. Folder missing: "{build_lang_path}"', prefix=os.linesep)
                continue

            if len(fnmatch.filter(os.listdir(build_lang_path), '*.xml')) == 0:
                Log.warn(f'Cannot build PAK. Folder empty or does not contain XML files: "{build_lang_path}"', prefix=os.linesep)
                continue

            lang_pak_file_name: str = build_lang_path + self.settings.pak_extension

            Log.info(f'Writing PAK: "{self.options.relpath(lang_pak_file_name)}"',
                     prefix=os.linesep, suffix=os.linesep + self.sep)

            if self.options.pack_assets:
                for filename in xml_files:
                    file_name: str = os.path.basename(filename)

                    if file_name in self.settings.localization:
                        continue

                    output_path: str = os.path.join(build_lang_path, file_name)

                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    shutil.copy2(filename, output_path)

                    Log.info(f'File copied for PAK: "{filename}"')
                    Log.debug(f'output_path="{output_path}"', prefix='\t')

            with ZipFileFixed(lang_pak_file_name, mode='w', compression=ZIP_STORED) as zip_file:
                build_lang_xml_glob: str = os.path.join(build_lang_path, '*.xml')

                for filename in glob.glob(build_lang_xml_glob, recursive=False):
                    arcname: str = os.path.relpath(filename, build_lang_path)
                    zip_file.write(filename, arcname)

                    Log.info(f'File added to PAK: "{self.options.relpath(filename)}"')
                    Log.debug(f'arcname="{arcname}"', prefix='\t')

    def pack(self) -> str:
        """Writes build assets to ZIP file. Returns output ZIP file path."""
        Log.info(f'Writing ZIP: "{self.options.relpath(self.settings.build_zip_file_path)}"',
                 prefix=os.linesep, suffix=os.linesep + self.sep)

        build_pak_glob: str = os.path.join(self.settings.build_zip_folder_path, '**\*.pak')
        project_pak_glob: str = os.path.join(self.settings.project_path, '**\*.pak')

        with ZipFileFixed(self.settings.build_zip_file_path, mode='w', compression=ZIP_DEFLATED) as zip_file:
            zip_file.write(self.settings.project_manifest_path, self.settings.zip_manifest_arc_name, compress_type=ZIP_DEFLATED)

            Log.info(f'File added to ZIP: "{self.options.relpath(self.settings.project_manifest_path)}"')
            Log.debug(f'arcname="{self.settings.zip_manifest_arc_name}"', prefix='\t')

            build_pak_files: list = glob.glob(build_pak_glob, recursive=True)

            project_pak_files: list = [f for f in glob.glob(project_pak_glob, recursive=True) if
                                       self.settings.project_build_path not in os.path.dirname(f)]

            for filename in build_pak_files + project_pak_files:
                if filename in project_pak_files:
                    arcname: str = os.path.join(self.settings.zip_name, self.options.relpath(filename))
                else:
                    arcname = os.path.relpath(filename, self.settings.project_build_path)

                zip_file.write(filename, arcname)

                Log.info(f'File added to ZIP: "{self.options.relpath(filename)}"')
                Log.debug(f'arcname="{arcname}"', prefix='\t')

        return self.settings.build_zip_file_path
