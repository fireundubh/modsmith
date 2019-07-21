import os
from dataclasses import dataclass, field
from winreg import EnumValue, HKEYType, HKEY_LOCAL_MACHINE, KEY_READ, OpenKey, QueryInfoKey


@dataclass
class Registry:
    installed_path: str = field(init=False, default_factory=lambda: '')

    def __post_init__(self) -> None:
        self.installed_path = self.get_installed_path()

    @staticmethod
    def get_installed_path() -> str:
        # noinspection Mypy
        """
        Retrieves installed path for game from Windows Registry.

        * Galaxy Path: HKEY_LOCAL_MACHINE/SOFTWARE/Wow6432Node/GOG.com/Games/1719198803/path
        * Steam Path: HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows/CurrentVersion/Uninstall/Steam App 379430/InstallLocation

        Raises FileNotFoundError if the installed path cannot be found.
        """

        subkey_data: list = [
            r'SOFTWARE/Wow6432Node/GOG.com/Games/1719198803/path',
            r'SOFTWARE/Microsoft/Windows/CurrentVersion/Uninstall/Steam App 379430/InstallLocation'
        ]

        for subkey in subkey_data:
            subkey_path, subkey_value_name = os.path.split(subkey)
            subkey_path = subkey_path.replace('/', '\\')

            try:
                key: HKEYType = OpenKey(HKEY_LOCAL_MACHINE, subkey_path, 0, KEY_READ)
            except FileNotFoundError:
                continue

            _, values, _ = QueryInfoKey(key)

            for i in range(0, values):
                value_name, value_data, _ = EnumValue(key, i)
                if value_name == subkey_value_name:
                    return value_data

        raise FileNotFoundError('Cannot find installed path for game')
