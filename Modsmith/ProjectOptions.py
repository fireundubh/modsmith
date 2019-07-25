import os

from argparse import Namespace
from dataclasses import dataclass, field

from lxml import etree

from Modsmith.Constants import XML_PARSER


@dataclass
class ProjectOptions:
    _args: Namespace = field(repr=False, default_factory=Namespace)

    manifest_path: str = field(init=False, default_factory=lambda: '')
    config_path: str = field(init=False, default_factory=lambda: '')
    project_path: str = field(init=False, default_factory=lambda: '')
    localization_path: str = field(init=False, default_factory=lambda: '')
    pak_file_name: str = field(init=False, default_factory=lambda: '')
    zip_file_name: str = field(init=False, default_factory=lambda: '')

    pack_assets: bool = field(init=False, default_factory=lambda: False)
    debug: bool = field(init=False, default_factory=lambda: False)

    def __post_init__(self) -> None:
        if not self._args.config_path:
            cwd: str = os.path.dirname(__file__)
            self._args.config_path = os.path.join(cwd, 'kingdomcome.yaml')

            if not os.path.exists(self._args.config_path):
                self._args.config_path = os.path.normpath(os.path.join(cwd, '..', 'kingdomcome.yaml'))

        for key in self.__dict__:
            if key in ('_args', 'project_path', 'localization_path', 'pak_file_name', 'zip_file_name'):
                continue
            user_value = getattr(self._args, key)
            if user_value != getattr(self, key):
                setattr(self, key, user_value)

        if not os.path.exists(self.manifest_path):
            return

        self.project_path = os.path.dirname(self.manifest_path)
        self.localization_path = os.path.join(self.project_path, 'Localization')

        try:
            tree: etree.ElementTree = etree.parse(self.manifest_path, parser=XML_PARSER)
        except etree.XMLSyntaxError as e:
            raise

        name_element, version_element = tree.xpath('//name'), tree.xpath('//version')

        project_name: str = name_element[0].text if name_element else os.path.basename(self.project_path)
        version_string: str = version_element[0].text if version_element else ''

        self.pak_file_name = project_name

        if not version_string:
            self.zip_file_name = project_name
        else:
            self.zip_file_name = '{}-v{}'.format(project_name.replace(' ', '_'), version_string.replace('.', '-'))

    def __setattr__(self, key: str, value: str) -> None:
        if value != '' and key not in ('_args', 'pack_assets', 'debug'):
            if key in ('manifest_path', 'config_path'):
                if isinstance(value, list):
                    value = value[0]
                if not os.path.exists(value):
                    return
            elif key == 'pak_file_name':
                if not value.endswith('.pak'):
                    value = value + '.pak'
            elif key == 'zip_file_name':
                if not value.endswith('.zip'):
                    value = value + '.zip'

        super(ProjectOptions, self).__setattr__(key, value)
