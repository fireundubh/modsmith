import os
from dataclasses import (dataclass,
                         field)

from yaml import (CLoader,
                  load)

from modsmith import (ProjectOptions,
                      Registry)


@dataclass
class ProjectSettings:
    options: ProjectOptions = field(init=True, default_factory=None)

    game_path: str = field(init=False, default_factory=lambda: '')
    project_manifest_path: str = field(init=False, default_factory=lambda: '')
    project_path: str = field(init=False, default_factory=lambda: '')
    project_data_path: str = field(init=False, default_factory=lambda: '')
    project_i18n_path: str = field(init=False, default_factory=lambda: '')
    project_build_path: str = field(init=False, default_factory=lambda: '')

    pak_extension: str = field(init=False, default_factory=lambda: '')

    zip_name: str = field(init=False, default_factory=lambda: '')
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
        self.project_manifest_path = self.options.manifest_path
        self.project_data_path = os.path.join(self.project_path, 'Data')
        self.project_build_path = os.path.join(self.project_path, 'Build')
        self.project_i18n_path = self.options.localization_path

        self.pak_file_name = self.options.pak_file_name[:-4]
        self.pak_extension = self.options.pak_file_name[-4:]

        # ---------------------------------------------------------------------
        # ZIP NAME AND EXTENSION
        # ---------------------------------------------------------------------
        self.zip_name = self.options.zip_file_name[:-4]

        # ---------------------------------------------------------------------
        # ZIP PATHS
        # ---------------------------------------------------------------------
        self.build_zip_file_path = os.path.join(self.project_build_path, self.options.zip_file_name)
        self.build_zip_folder_path = os.path.join(self.project_build_path, self.pak_file_name)

        self.build_data_path = os.path.join(self.build_zip_folder_path, 'Data')
        self.build_localization_path = os.path.join(self.build_zip_folder_path, 'Localization')

        self.build_package_path = os.path.join(self.build_data_path, self.options.pak_file_name)

        self.zip_manifest_arc_name = os.path.join(self.pak_file_name, 'mod.manifest')

        # ---------------------------------------------------------------------
        # DATABASE INITIALIZATION
        # ---------------------------------------------------------------------
        with open(self.options.config_path, mode='r') as f:
            db: dict = load(f, Loader=CLoader)

        self.exclusions: list = db['Exclusions']
        self.localization: list = db['Localization']
        self.packages: dict = db['Packages']
        self.signatures: list = db['Signatures']

    def make_project_relative(self, path: str) -> str:
        return os.path.relpath(path, self.project_path)
