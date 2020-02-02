import argparse
import glob
import logging
import os
import shutil
import subprocess
import sys
import zipfile


class Application:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname).4s] %(message)s')
    log: logging.Logger = logging.getLogger('modsmith')

    def __init__(self, args: argparse.Namespace) -> None:
        self.root_path: str = os.path.dirname(__file__)

        self.pipenv_cmd: str = args.pipenv_cmd
        self.package_name: str = 'modsmith'
        self.no_zip: bool = args.no_zip
        self.vcvars64_path: str = args.vcvars64_path

        self.dist_path: str = os.path.join(self.root_path, f'{self.package_name}.dist')
        self.root_tools_path: str = os.path.join(self.root_path, 'kingdomcome.yaml')
        self.dist_tools_path: str = os.path.join(self.dist_path, 'kingdomcome.yaml')

    def __setattr__(self, key: str, value: object) -> None:
        # sanitize paths
        if isinstance(value, str) and key.endswith('path'):
            value = os.path.normpath(value)
            # normpath converts empty paths to os.curdir which we don't want
            if value == '.':
                value = ''
        super(Application, self).__setattr__(key, value)

    def _clean_dist_folder(self) -> None:
        if not os.path.exists(self.dist_path):
            return

        files_to_keep: tuple = (
            f'{self.package_name}.exe',
            'libffi-7.dll',
            'python38.dll',
            '_ctypes.pyd',
            '_elementpath.pyd',
            '_yaml.pyd',
            'etree.pyd'
        )

        files: list = [f for f in glob.iglob(os.path.join(self.dist_path, r'**\*'), recursive=True)
                       if os.path.isfile(f) and not f.endswith(files_to_keep)]

        for f in files:
            Application.log.warning(f'Deleting: "{f}"')
            os.remove(f)

        site_dir: str = os.path.join(self.dist_path, 'site')
        if os.path.exists(site_dir):
            shutil.rmtree(site_dir, ignore_errors=True)

    def _build_zip_archive(self) -> str:
        zip_path: str = os.path.join(self.root_path, 'bin', f'{self.package_name}.zip')
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)

        files: list = [f for f in glob.glob(os.path.join(self.dist_path, r'**\*'), recursive=True) if os.path.isfile(f)]

        with zipfile.ZipFile(zip_path, 'w') as z:
            for f in files:
                z.write(f, os.path.join(self.package_name, os.path.relpath(f, self.dist_path)), compress_type=zipfile.ZIP_STORED)
                Application.log.info(f'Added file to archive: {f}')

        return zip_path

    def run(self) -> int:
        if not sys.platform == 'win32':
            Application.log.error('Cannot build with Nuitka on a non-Windows platform')
            sys.exit(1)

        if self.vcvars64_path:
            if not os.path.exists(self.vcvars64_path) or not self.vcvars64_path.endswith('.bat'):
                Application.log.error('Cannot build with MSVC compiler because VsDevCmd path is invalid')
                sys.exit(1)

        Application.log.info(f'Using project path: "{self.root_path}"')

        Application.log.warning(f'Cleaning: "{self.dist_path}"')
        shutil.rmtree(self.dist_path, ignore_errors=True)
        os.makedirs(self.dist_path, exist_ok=True)

        fail_state: int = 0

        env_log_path: str = ''
        environ: dict = os.environ.copy()

        if self.vcvars64_path:
            try:
                process = subprocess.Popen(f'%comspec% /C "{self.vcvars64_path}"', stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            except FileNotFoundError:
                fail_state = 1

            # noinspection PyUnboundLocalVariable
            while process.poll() is None:
                line: str = process.stdout.readline().strip()
                Application.log.info(line)

                if 'post-execution' in line:
                    _, env_log_path = line.split(' to ')
                    process.terminate()

            Application.log.info(f'Loading environment: "{env_log_path}"')

            with open(env_log_path, encoding='utf-8') as f:
                lines: list = f.read().splitlines()

                for line in lines:
                    key, value = line.split('=', maxsplit=1)
                    environ[key] = value

        args: list = [
            self.pipenv_cmd, 'run', 'python', '-m', 'nuitka',
            '--standalone', self.package_name,
            f'--include-package={self.package_name}',
            '--experimental=use_pefile',
            '--python-flag=nosite',
            f'--python-for-scons={sys.executable}',
            '--assume-yes-for-downloads',
            # '--plugin-enable=multiprocessing',
            '--show-progress',
            '--file-reference-choice=runtime'
        ]

        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, env=environ)
        except FileNotFoundError:
            Application.log.error(f'Cannot run command: {" ".join(args)}')
            fail_state = 1

        if fail_state == 0:
            # noinspection PyUnboundLocalVariable
            while process.poll() is None:
                line = process.stdout.readline().strip()

                if not line:
                    continue

                if line.startswith(('Courtesy Notice', 'Executing', 'Nuitka:INFO:Optimizing', 'Nuitka:INFO:Doing', 'Nuitka:INFO:Demoting')):
                    continue

                if line.startswith('Error, cannot locate suitable C compiler'):
                    Application.log.error('Cannot locate suitable C compiler.')
                    fail_state = 1
                    break

                if line.startswith('Error, mismatch between') and 'arches' in line:
                    _, message = line.split('between')
                    Application.log.error(f'Cannot proceed with mismatching architectures: {message.replace(" arches", "")}')
                    fail_state = 1
                    break

                if line.startswith('Error'):
                    Application.log.error(line)
                    fail_state = 1
                    break

                if line.startswith('Nuitka:INFO'):
                    line = line.replace('Nuitka:INFO:', '')

                if line.startswith('PASS 2'):
                    line = 'PASS 2:'

                Application.log.info(line)

        if fail_state == 0 and not os.path.exists(self.dist_path) or f'{self.package_name}.exe' not in os.listdir(self.dist_path):
            Application.log.error(f'Cannot find {self.package_name}.exe in folder or folder does not exist: {self.dist_path}')
            fail_state = 1

        if fail_state == 0:
            Application.log.info('Removing unnecessary files...')
            self._clean_dist_folder()

            Application.log.info('Copying YAML...')
            shutil.copy2(self.root_tools_path, self.dist_tools_path)

            if not self.no_zip:
                Application.log.info('Building archive...')
                zip_created: str = self._build_zip_archive()

                Application.log.info(f'Wrote archive: "{zip_created}"')

            Application.log.info('Build complete.')

            return fail_state

        Application.log.error(f'Failed to execute command: {" ".join(args)}')

        Application.log.warning(f'Resetting: "{self.dist_path}"')
        shutil.rmtree(self.dist_path, ignore_errors=True)

        return fail_state


if __name__ == '__main__':
    _parser = argparse.ArgumentParser(description='Modsmith Build Script')

    _parser.add_argument('--pipenv-cmd',
                         action='store', default='pipenv',
                         help='command to use for pipenv')

    _parser.add_argument('--no-zip',
                         action='store_true', default=False,
                         help='do not create zip archive')

    _parser.add_argument('--vcvars64-path',
                         action='store', default='',
                         help='path to visual studio developer command prompt')

    Application(_parser.parse_args()).run()
