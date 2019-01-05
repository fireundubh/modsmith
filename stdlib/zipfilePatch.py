import struct
from zipfile import (BadZipFile, ZIP_STORED, ZipExtFile, ZipFile, ZipInfo, _FH_EXTRA_FIELD_LENGTH, _FH_FILENAME_LENGTH, _FH_SIGNATURE, _SharedFile,
                     _ZipDecrypter, sizeFileHeader, stringFileHeader, structFileHeader)


class ZipFileFixed(ZipFile):
    # def __init__(self, file, mode='r', compression=ZIP_STORED, allowZip64=True, compresslevel=None):
    #     super().__init__(file, mode, compression, allowZip64, compresslevel)
    #
    # def __enter__(self):
    #     super(ZipFileFixed, self).__enter__()
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     super(ZipFileFixed, self).__exit__(exc_type, exc_val, exc_tb)
    #
    # def __repr__(self):
    #     super(ZipFileFixed, self).__repr__()

    def open(self, name, mode='r', pwd=None, *, force_zip64=False):
        if mode not in {'r', 'w'}:
            raise ValueError('open() requires mode "r" or "w"')
        if pwd and not isinstance(pwd, bytes):
            raise TypeError(f'pwd: expected bytes, got {type(pwd).__name__}')
        if pwd and (mode == 'w'):
            raise ValueError('pwd is only supported for reading files')
        if not self.fp:
            raise ValueError('Attempt to use ZIP archive that was already closed')

        # Make sure we have an info object
        if isinstance(name, ZipInfo):
            # 'name' is already an info object
            zinfo = name
        elif mode == 'w':
            zinfo = ZipInfo(name)
            zinfo.compress_type = self.compression
            zinfo._compresslevel = self.compresslevel
        else:
            # Get info object for name
            zinfo = self.getinfo(name)

        if mode == 'w':
            return self._open_to_write(zinfo, force_zip64=force_zip64)

        if self._writing:
            raise ValueError("Can't read from the ZIP file while there "
                             "is an open writing handle on it. "
                             "Close the writing handle before trying to read.")

        # Open for reading:
        self._fileRefCnt += 1
        zef_file = _SharedFile(self.fp, zinfo.header_offset,
                               self._fpclose, self._lock, lambda: self._writing)
        try:
            # Skip the file header:
            fheader = zef_file.read(sizeFileHeader)
            if len(fheader) != sizeFileHeader:
                raise BadZipFile('Truncated file header')
            fheader = struct.unpack(structFileHeader, fheader)
            if fheader[_FH_SIGNATURE] != stringFileHeader:
                raise BadZipFile('Bad magic number for file header')

            # FIX(fireundubh): removed var declaration due to fix making var unused
            zef_file.read(fheader[_FH_FILENAME_LENGTH])
            if fheader[_FH_EXTRA_FIELD_LENGTH]:
                zef_file.read(fheader[_FH_EXTRA_FIELD_LENGTH])

            if zinfo.flag_bits & 0x20:
                # Zip 2.7: compressed patched data
                raise NotImplementedError('compressed patched data (flag bit 5)')

            if zinfo.flag_bits & 0x40:
                # strong encryption
                raise NotImplementedError('strong encryption (flag bit 6)')

            # FIX(fireundubh): removed opinionated encoding test that breaks shit
            # See: https://bugs.python.org/issue6839

            # check for encrypted flag & handle password
            is_encrypted = zinfo.flag_bits & 0x1
            zd = None
            if is_encrypted:
                if not pwd:
                    pwd = self.pwd
                if not pwd:
                    raise RuntimeError(f'File {name!r} is encrypted, password required for extraction')

                zd = _ZipDecrypter(pwd)
                header = zef_file.read(12)
                h = zd(header[0:12])
                if zinfo.flag_bits & 0x8:
                    # compare against the file type from extended local headers
                    check_byte = (zinfo._raw_time >> 8) & 0xff
                else:
                    # compare against the CRC otherwise
                    check_byte = (zinfo.CRC >> 24) & 0xff
                if h[11] != check_byte:
                    raise RuntimeError(f'Bad password for file {name!r}')

            return ZipExtFile(zef_file, mode, zinfo, zd, True)
        except:
            zef_file.close()
            raise
