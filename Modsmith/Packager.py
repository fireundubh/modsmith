import fnmatch
import glob
import operator
import os
import shutil
from functools import reduce
from typing import Generator
from zipfile import (ZIP_DEFLATED,
                     ZIP_STORED)

from modsmith import (Patcher,
                      ProjectSettings,
                      SimpleLogger as Log,
                      ZipFileFixed)


class Packager:
    def __init__(self, settings: ProjectSettings) -> None:
        self.settings: ProjectSettings = settings
        self.sep = '-' * 80

        self.project_glob_all = os.path.join(self.settings.project_data_path, r'**\*')
        self.project_glob_paks: str = os.path.join(self.settings.project_path, r'**\*.pak')
        self.build_glob_paks: str = os.path.join(self.settings.build_zip_folder_path, r'**\*.pak')

    @staticmethod
    def _copy_assets_to_build_path(xml_files: list, build_lang_path: str, excluded_files: list) -> None:
        for filename in xml_files:
            base_name: str = os.path.basename(filename)

            if base_name in excluded_files:
                continue

            # TODO: check if we need to dirname
            output_file_path: str = os.path.join(build_lang_path, base_name)

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            shutil.copy2(filename, output_file_path)

            Log.info(f'File copied for PAK: "{filename}"')
            Log.debug(f'output_file_path="{output_file_path}"', prefix='\t')

    def _prepare_i18n_targets(self, folders: list) -> list:
        """Generates a list i18n XML files, and creates output directories if needed"""

        xml_files: list = []

        for folder in folders:
            for f in glob.iglob(os.path.join(self.settings.project_i18n_path, folder, '*.xml'), recursive=False):
                os.makedirs(os.path.join(self.settings.build_localization_path, folder), exist_ok=True)
                xml_files.append(f)

        return xml_files

    def _generate_file_list(self, files_supported: set, files_unsupported: set, files_misc: set) -> Generator:
        for supported_file in files_supported:
            arcname: str = os.path.relpath(supported_file, self.settings.project_data_path)
            target_file: str = os.path.join(self.settings.build_data_path, arcname)
            yield target_file, arcname

        for unsupported_file in files_unsupported.union(files_misc):
            if unsupported_file.endswith('.tbl'):
                continue
            target_arcname = os.path.relpath(unsupported_file, self.settings.project_data_path)
            yield unsupported_file, target_arcname

    def generate_pak(self) -> None:
        project_files = [f for f in glob.iglob(self.project_glob_all, recursive=True)
                         if os.path.isfile(f) and not f.endswith('.pak') and not f.endswith('.tbl')]

        # we only care about xml files for patching and tbl generation
        project_files_xml = [f for f in project_files if f.endswith('.xml')]

        # separate supported and unsupported files
        project_files_xml_supported = set(f for f in project_files_xml
                                          if not any(x.lower() in f.lower() for x in self.settings.exclusions))

        project_files_xml_unsupported = set(project_files_xml) - set(project_files_xml_supported)

        # separate non-xml files from xml files
        project_files_other = set(project_files) - set(project_files_xml)

        Log.info('Patching game data...',
                 prefix=os.linesep,
                 suffix=os.linesep + self.sep)

        patcher: Patcher = Patcher(self.settings)
        patcher.patch_data(list(project_files_xml_supported))

        Log.info('Writing PAK: "%s"' % self.settings.make_project_relative(self.settings.build_package_path),
                 prefix=os.linesep,
                 suffix=os.linesep + self.sep)

        target_folder = os.path.dirname(self.settings.build_package_path)
        os.makedirs(target_folder, exist_ok=True)

        with ZipFileFixed(self.settings.build_package_path, 'w', ZIP_STORED) as zip_file:
            for filename, arcname in self._generate_file_list(project_files_xml_supported,
                                                              project_files_xml_unsupported, project_files_other):
                base_name = os.path.basename(arcname)

                if '__' not in base_name:
                    file_name, file_extension = os.path.splitext(base_name)

                    arcname = '%s%s__%s%s' % (arcname[:-len(base_name)],
                                              file_name,
                                              self.settings.pak_file_name.lower().replace(' ', '_'),
                                              file_extension)

                zip_file.write(filename, arcname)

                Log.info('File added to PAK: "%s"' % self.settings.make_project_relative(filename))
                Log.debug(f'arcname="{arcname}"', prefix='\t')

    def generate_i18n(self) -> None:
        folder_names: list = os.listdir(self.settings.project_i18n_path)
        xml_files: list = self._prepare_i18n_targets(folder_names)

        try:
            reduce(operator.concat, xml_files)
        except TypeError:
            Log.error('Failed to prepare i18n targets.')
            if folder_names:
                Log.info(r'Is your folder structure correct? (e.g., Localization\english_xml\*.xml)',
                         prefix='\t',
                         suffix=os.linesep)
            raise

        Log.info('Patching localization...',
                 prefix=os.linesep,
                 suffix=os.linesep + self.sep)

        patcher: Patcher = Patcher(self.settings)
        patcher.patch_localization(xml_files)

        for folder_name in folder_names:
            build_lang_path = os.path.join(self.settings.build_localization_path, folder_name)
            glob_build_lang_xml = os.path.join(build_lang_path, '*.xml')

            if not os.path.exists(build_lang_path):
                Log.warn(f'Cannot build PAK. Folder missing: "{build_lang_path}"',
                         prefix=os.linesep)
                continue

            lang_files = os.listdir(build_lang_path)
            lang_files_xml = fnmatch.filter(lang_files, '*.xml')
            if len(lang_files_xml) == 0:
                Log.warn(f'Cannot build PAK. Folder empty or does not contain XML files: "{build_lang_path}"',
                         prefix=os.linesep)
                continue

            lang_pak_file_name = build_lang_path + self.settings.pak_extension

            Log.info('Writing PAK: "%s"' % self.settings.make_project_relative(lang_pak_file_name),
                     prefix=os.linesep,
                     suffix=os.linesep + self.sep)

            if self.settings.options.pack_assets:
                self._copy_assets_to_build_path(xml_files, build_lang_path, self.settings.localization)

            target_folder = os.path.dirname(lang_pak_file_name)
            os.makedirs(target_folder, exist_ok=True)

            with ZipFileFixed(lang_pak_file_name, 'w', ZIP_STORED) as zip_file:
                for filename in glob.iglob(glob_build_lang_xml, recursive=False):
                    arcname: str = os.path.relpath(filename, build_lang_path)

                    base_name = os.path.basename(arcname)

                    if '__' not in base_name:
                        file_name, file_extension = os.path.splitext(base_name)

                        arcname = '%s%s__%s%s' % (arcname[:-len(base_name)],
                                                  file_name,
                                                  self.settings.pak_file_name.lower().replace(' ', '_'),
                                                  file_extension)

                    zip_file.write(filename, arcname)

                    Log.info(f'File added to PAK: "{self.settings.make_project_relative(filename)}"')
                    Log.debug(f'arcname="{arcname}"',
                              prefix='\t')

    def pack(self) -> str:
        """Writes build assets to ZIP file. Returns output ZIP file path."""

        Log.info(f'Writing ZIP: "{self.settings.make_project_relative(self.settings.build_zip_file_path)}"',
                 prefix=os.linesep,
                 suffix=os.linesep + self.sep)

        target_folder = os.path.dirname(self.settings.build_zip_file_path)
        os.makedirs(target_folder, exist_ok=True)

        with ZipFileFixed(self.settings.build_zip_file_path, 'w', ZIP_DEFLATED) as zip_file:
            zip_file.write(self.settings.project_manifest_path, self.settings.zip_manifest_arc_name, ZIP_DEFLATED)

            Log.info(f'File added to ZIP: "{self.settings.make_project_relative(self.settings.project_manifest_path)}"')
            Log.debug(f'arcname="{self.settings.zip_manifest_arc_name}"',
                      prefix='\t')

            build_pak_files: list = glob.glob(self.build_glob_paks, recursive=True)

            project_pak_files: list = [f for f in glob.iglob(self.project_glob_paks, recursive=True)
                                       if self.settings.project_build_path not in os.path.dirname(f)]

            for filename in build_pak_files + project_pak_files:
                if filename in project_pak_files:
                    arcname = os.path.join(self.settings.pak_file_name, self.settings.make_project_relative(filename))
                else:
                    arcname = os.path.relpath(filename, self.settings.project_build_path)

                zip_file.write(filename, arcname)

                Log.info(f'File added to ZIP: "{self.settings.make_project_relative(filename)}"')
                Log.debug(f'arcname="{arcname}"',
                          prefix='\t')

        return self.settings.build_zip_file_path
