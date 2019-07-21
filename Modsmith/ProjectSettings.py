import os
from dataclasses import dataclass, field

import yaml

from Modsmith.ProjectOptions import ProjectOptions
from Modsmith.Registry import Registry


@dataclass
class ProjectSettings:
    options: ProjectOptions = field(init=True, default_factory=None)

    game_path: str = field(init=False, default_factory=lambda: '')
    project_manifest_path: str = field(init=False, default_factory=lambda: '')
    project_path: str = field(init=False, default_factory=lambda: '')
    project_data_path: str = field(init=False, default_factory=lambda: '')
    project_localization_path: str = field(init=False, default_factory=lambda: '')
    project_build_path: str = field(init=False, default_factory=lambda: '')

    pak_name: str = field(init=False, default_factory=lambda: '')
    pak_extension: str = field(init=False, default_factory=lambda: '')

    zip_file_name: str = field(init=False, default_factory=lambda: '')
    zip_name: str = field(init=False, default_factory=lambda: '')
    zip_extension: str = field(init=False, default_factory=lambda: '')
    zip_manifest_arc_name: str = field(init=False, default_factory=lambda: '')

    build_data_path: str = field(init=False, default_factory=lambda: '')
    build_package_path: str = field(init=False, default_factory=lambda: '')
    build_localization_path: str = field(init=False, default_factory=lambda: '')
    build_zip_file_path: str = field(init=False, default_factory=lambda: '')
    build_zip_folder_path: str = field(init=False, default_factory=lambda: '')

    exclusions: list = field(init=False, default_factory=list)
    localization: list = field(init=False, default_factory=list)
    packages: list = field(init=False, default_factory=list)
    signatures: list = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        """Sets up the necessary paths for building PAKs"""

        self.game_path = Registry.get_installed_path()

        self.project_path = self.options.project_path
        self.project_manifest_path = os.path.join(self.project_path, 'mod.manifest')
        self.project_data_path = os.path.join(self.project_path, 'Data')
        self.project_build_path = os.path.join(self.project_path, 'Build')

        if not self.options.localization_path:
            self.project_localization_path = os.path.join(self.project_path, 'Localization')
        else:
            self.project_localization_path = self.options.localization_path

        self.pak_name, self.pak_extension = os.path.splitext(self.options.pak_file_name)

        # ---------------------------------------------------------------------
        # ZIP NAME AND EXTENSION
        # ---------------------------------------------------------------------
        self.zip_file_name = self.options.zip_file_name
        self.zip_name, self.zip_extension = os.path.splitext(self.options.zip_file_name)

        # ---------------------------------------------------------------------
        # ZIP PATHS
        # ---------------------------------------------------------------------
        self.build_zip_file_path = os.path.join(self.project_build_path, self.zip_file_name)
        self.build_zip_folder_path = os.path.join(self.project_build_path, self.zip_name)

        self.build_data_path = os.path.join(self.build_zip_folder_path, 'Data')
        self.build_localization_path = os.path.join(self.build_zip_folder_path, 'Localization')

        self.build_package_path = os.path.join(self.build_data_path, self.options.pak_file_name)

        self.zip_manifest_arc_name = os.path.join(self.zip_name, 'mod.manifest')

        # ---------------------------------------------------------------------
        # DATABASE INITIALIZATION
        # ---------------------------------------------------------------------
        with open(self.options.config_path, mode='r') as f:
            db = yaml.load(f, Loader=yaml.CLoader)

        self.exclusions: list = db['Exclusions']
        self.localization: list = db['Localization']
        self.packages: dict = db['Packages']
        self.signatures: list = db['Signatures']