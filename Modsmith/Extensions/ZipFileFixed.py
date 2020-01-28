import struct

from zipfile import (BadZipFile,
                     ZipExtFile,
                     ZipFile,
                     ZipInfo,
                     _SharedFile,
                     sizeFileHeader,
                     stringFileHeader,
                     structFileHeader)


# noinspection Mypy
class ZipFileFixed(ZipFile):
    def open(self, name: str, mode: str = 'r', pwd: bytes = None, *, force_zip64: bool = False) -> ZipExtFile:
        if not self.fp:
            raise ValueError('Attempt to use ZIP archive that was already closed')

        if isinstance(name, ZipInfo):
            zinfo = name
        elif mode == 'w':
            zinfo = ZipInfo(name)
            zinfo.compress_type = self.compression
            zinfo._compresslevel = self.compresslevel
        else:
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
            fheader = zef_file.read(sizeFileHeader)
            if len(fheader) != sizeFileHeader:
                raise BadZipFile('Truncated file header')

            fheader = struct.unpack(structFileHeader, fheader)
            if fheader[0] != stringFileHeader:
                raise BadZipFile('Bad magic number for file header')

            zef_file.read(fheader[10])
            if fheader[11]:
                zef_file.read(fheader[11])

            return ZipExtFile(zef_file, mode, zinfo, None, True)
        except:
            zef_file.close()
            raise
