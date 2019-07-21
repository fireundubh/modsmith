import os
from argparse import Namespace
from dataclasses import dataclass, field


@dataclass
class ProjectOptions:
    _args: Namespace = field(repr=False, default_factory=Namespace)

    config_path: str = field(init=False, default_factory=lambda: '')
    project_path: str = field(init=False, default_factory=lambda: '')
    localization_path: str = field(init=False, default_factory=lambda: '')
    pak_file_name: str = field(init=False, default_factory=lambda: '')
    zip_file_name: str = field(init=False, default_factory=lambda: '')

    pack_assets: bool = field(init=False, default_factory=lambda: False)
    debug: bool = field(init=False, default_factory=lambda: False)

    def __post_init__(self) -> None:
        for key in self.__dict__:
            if key == '_args':
                continue
            user_value = getattr(self._args, key)
            if user_value != getattr(self, key):
                setattr(self, key, user_value)

    def __setattr__(self, key: str, value: str) -> None:
        if value != '' and key not in ('_args', 'pack_assets', 'debug'):
            if key in ('config_path', 'project_path', 'localization_path'):
                if not os.path.exists(value):
                    return
            elif key == 'pak_file_name':
                if not value.endswith('.pak'):
                    value = value + '.pak'
            elif key == 'zip_file_name':
                if not value.endswith('.zip'):
                    value = value + '.zip'

        super(ProjectOptions, self).__setattr__(key, value)
