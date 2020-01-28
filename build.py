import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from glob import glob


class Application:
    def __init__(self, args: argparse.Namespace) -> None:
        self.cwd: str = os.getcwd()

        if os.path.exists(args.nuitka_path):
            self.nuitka_path = args.nuitka_path
        else:
            raise FileNotFoundError(args.nuitka_path)

        self.package_name = args.package_name

    def _clean_dist_folder(self, path: str) -> None:
        files_to_keep: tuple = (
            '%s.exe' % self.package_name,
            '_ctypes.pyd',
            '_elementpath.pyd',
            '_yaml.pyd',
            'etree.pyd',
            'python37.dll',
            'unicodedata.pyd',
        )

        if not os.path.exists(path):
            return

        files: list = [f for f in glob(os.path.join(path, r'**\*'), recursive=True)
                       if os.path.isfile(f) and not f.endswith(files_to_keep)]

        for f in files:
            os.remove(f)
            print('Deleted: %s' % f)

        try:
            lxml_html_path: str = os.path.join(path, 'lxml', 'html')
            os.rmdir(lxml_html_path)
            print('Deleted: %s' % lxml_html_path)
        except (FileNotFoundError, OSError):
            pass

    def _copy_yaml_to_dist_folder(self, path: str) -> str:
        src: str = os.path.join(self.cwd, 'kingdomcome.yaml')
        dst: str = os.path.join(path, os.path.basename(src))
        if not os.path.exists(dst):
            return shutil.copy2(src, dst)
        raise FileNotFoundError(f'Cannot find destination file: {dst}')

    def _build_zip_archive(self, path: str) -> str:
        zip_file: str = f'{self.package_name}.zip'
        zip_path: str = os.path.join(self.cwd, 'bin', zip_file)

        files: list = [f for f in glob(os.path.join(path, r'**\*'), recursive=True) if os.path.isfile(f)]

        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, os.path.relpath(f, path), compress_type=zipfile.ZIP_DEFLATED)
                print(f'Added file to archive: {f}')

        return zip_path

    def run(self) -> int:
        package_path: str = os.path.join(self.cwd, self.package_name)

        dist_folder: str = os.path.join(self.cwd, f'{self.package_name}.dist')
        if os.path.exists(dist_folder):
            shutil.rmtree(dist_folder, ignore_errors=True)

        # noinspection PyListCreation
        args: list = [
            self.nuitka_path,
            '--standalone',
            '--experimental=use_pefile',
            '--python-flag=no_site',
            '--python-flag=nosite',
            '--python-for-scons=%s' % sys.executable,
            '--assume-yes-for-downloads',
            '--mingw64',
            '--show-progress',
            '--show-scons'
        ]

        args.append('--output-dir=%s' % self.cwd)
        args.append('%s' % package_path)

        retcode: int = subprocess.call(args)
        if retcode != 0:
            return retcode

        print('Cleaning up dist folder...')
        self._clean_dist_folder(dist_folder)

        file_copied: str = self._copy_yaml_to_dist_folder(dist_folder)
        print(f'Copied file to dist folder: {file_copied}')

        print('Building archive...')
        zip_created: str = self._build_zip_archive(dist_folder)
        print(f'Wrote archive: {zip_created}')

        return 0


if __name__ == '__main__':
    _parser = argparse.ArgumentParser()
    _parser.add_argument('-n', '--nuitka-path', action='store', type=str, default=r'D:\dev\python\3_7_4\Scripts\nuitka3.exe')
    _parser.add_argument('-p', '--package-name', action='store', type=str, default='Modsmith')
    Application(_parser.parse_args()).run()
