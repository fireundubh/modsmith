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
        cwd: str = os.path.dirname(__file__)

        self.config_path = os.path.join(cwd, 'kingdomcome.yaml')
        if not os.path.exists(self.config_path):
            self.config_path = os.path.normpath(os.path.join(cwd, '..', 'kingdomcome.yaml'))

        self.manifest_path = self._args.manifest_path
        if not os.path.exists(self.manifest_path):
            return

        self.project_path = os.path.dirname(self.manifest_path)
        self.localization_path = os.path.join(self.project_path, 'Localization')

        tree: etree.ElementTree = etree.parse(self.manifest_path, parser=XML_PARSER)
        name_element, version_element = tree.xpath('//name'), tree.xpath('//version')

        project_name: str = name_element[0].text if name_element else os.path.basename(self.project_path)
        version_string: str = version_element[0].text if version_element else ''

        self.pak_file_name = project_name

        if not version_string:
            self.zip_file_name = project_name.replace(' ', '_')
        else:
            self.zip_file_name = '{}_v{}'.format(project_name.replace(' ', '_'), version_string.replace('.', '-'))

    def __setattr__(self, key: str, value: str) -> None:
        if value != '' and key in ('manifest_path', 'config_path', 'pak_file_name', 'zip_file_name'):
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
