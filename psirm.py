#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Photo shop Icon Resources Manipulator - Modifies photo shop icon resource files

"Photo shop Icon Resources Manipulator - Modifies photo shop icon resource files"

# Based on information from https://github.com/stevenvi/photoshop-resource-editor
# Programmed by CoolCat467

__title__ = 'Photoshop Icon Resources Manipulator'
__author__ = 'CoolCat467'
__version__ = '0.0.0'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 0

from typing import Final, Generator, Iterable, cast

import io
import os
import sys
import struct
import dataclasses
from collections import deque

IDX_HEADER: Final              = 'Photoshop Icon Resource Index 1.0\n'
DATAFILE_NAME_LENGTH: Final    = 128
IMAGE_DATA_BLOCK_LENGTH: Final = 368

def read_string(string_data: bytes) -> str:
    "Decode null terminated string"
    return string_data.split(b'\x00', 1)[0].decode('utf-8')

def read_int(int_data: bytes) -> int:
    "Read integer"
    return cast(int, struct.unpack('<I', int_data)[0])

def write_string(string: str, padding: int) -> bytes:
    "Encode null terminated string"
    string_bytes = string.encode('utf-8')
    length = padding - len(string_bytes)
    if length < 0:
        length = 1
    return string_bytes + b'\x00' * length

def write_int(integer: int) -> bytes:
    "Write integer"
    return struct.pack('<I', integer)

@dataclasses.dataclass(slots = True)
class ImageMetadata:
    "Image metadata class"
    data: bytearray

    @property
    def name(self) -> str:
        "File name"
        return read_string(self.data[0:48])
    @name.setter
    def name(self, value: str) -> None:
        for idx, byte in enumerate(write_string(value, 48)):
            self.data[idx] = byte

    @staticmethod
    def __int_field(offset: int, doc: str) -> property:
        def get_v(self: 'ImageMetadata') -> int:
            return read_int(self.data[offset : offset+4])
        def set_v(self: 'ImageMetadata', value: int) -> None:
            if get_v(self) != value:
                print(f'Field "{doc}" in "{self.name}" changed to {value} (old = {get_v(self)})')
            for idx, byte in enumerate(write_int(value)):
                self.data[offset+idx] = byte
        return property(get_v, set_v, None, doc)

    width_low     = __int_field(48, 'Width of low')
    width_high    = __int_field(52, 'Width of high')
    length_low    = __int_field(64, 'Length of low')
    length_high   = __int_field(68, 'Length of high')
    off_low       = __int_field(112, 'Offset of low')
    off_low_old   = __int_field(136, 'Offset of low_old')
    off_high      = __int_field(144, 'Offset of high')
    off_high_old  = __int_field(168, 'Offset of high_old')
    size_low      = __int_field(240, 'Size of low')
    size_low_old  = __int_field(264, 'Size of low_old')
    size_high     = __int_field(272, 'Size of high')
    size_high_old = __int_field(296, 'Size of high_old')

    def set_dimensions(self, rtype: int, dimensions: tuple[int, int]) -> None:
        "Set dimensions"
        attrtype = ('low', 'high')[rtype%2]
        for name, value in zip(('width', 'length'), dimensions):
            setattr(self, f'{name}_{attrtype}', value)

    def set_position(self, rtype: int, dimensions: tuple[int, int]) -> None:
        "Set position (offset, size)"
        attrtype = ('low', 'high')[rtype%2]
        for name, value in zip(('off', 'size'), dimensions):
            setattr(self, f'{name}_{attrtype}', value)

    def get_position(self, rtype: int) -> tuple[int, int]:
        "Get position (offset, size)"
        attrtype = ('low', 'high')[rtype%2]
        data = []
        for name in ('off', 'size'):
            data.append(cast(int, getattr(self, f'{name}_{attrtype}')))
        off, size = data# pylint: disable=unbalanced-tuple-unpacking
        return off, size

def unpack_metadata(file: io.IOBase) -> ImageMetadata | None:
    "Unpack metadata from file"
    byte_data = file.read(IMAGE_DATA_BLOCK_LENGTH)
    if not byte_data:
        return None
    return ImageMetadata(bytearray(byte_data))

def pack_metadata(file: io.IOBase, metadata: ImageMetadata) -> None:
    "Pack metadata to file"
    file.write(metadata.data)

def unpack_index(filename: str) -> Generator[str | ImageMetadata, None, None]:
    "Unpack index"
    with open(filename, 'rb') as file:
        header = file.readline().decode('utf-8')
        if header != IDX_HEADER:
            print(f'Header "{header}" is not valid')
        yield read_string(file.read(DATAFILE_NAME_LENGTH))
        yield read_string(file.read(DATAFILE_NAME_LENGTH))
        yield read_string(file.read(DATAFILE_NAME_LENGTH))
        yield read_string(file.read(DATAFILE_NAME_LENGTH))
        while value := unpack_metadata(file):
            yield value

def ensure_path_exists(filepath: str) -> None:
    "Ensure full folder structure to file path given exists. If not exists, creates it."
    filepath = os.path.abspath(filepath)
    # Folder we want to ensure exists.
    folder = os.path.dirname(filepath)
    # If folder not exist
    if not os.path.exists(folder):
        # Ensure above folder exists
        ensure_path_exists(folder)
        # Make folder
        os.mkdir(folder)

def pack_index(filename: str,
               files: tuple[str, str, str, str],
               metadata: Iterable[ImageMetadata]) -> None:
    "Pack index"
    with open(filename, 'wb') as file:
        file.write(IDX_HEADER.encode('utf-8'))
        for dat_file in (files[i] for i in range(4)):
            file.write(write_string(dat_file, DATAFILE_NAME_LENGTH-1)+b'\n')
        for image in metadata:
            pack_metadata(file, image)

def extract_resource(resource_type: int,
                     resource_files: tuple[str, ...],
                     metadata: ImageMetadata,
                     base_folder: str) -> bool:
    "Extract resource from resource file given metadata"
    resource_type %= 2
    resource_type_name = ('Low', 'High')[resource_type]

    filename = os.path.join(base_folder, resource_type_name, f'{metadata.name}.png')
    offset, length = metadata.get_position(resource_type)

    if length == 0:
        return False

    ensure_path_exists(filename)
    with open(resource_files[resource_type], 'rb') as resource_file:
        resource_file.seek(offset)
        with open(filename, 'wb') as resource:
            resource.write(resource_file.read(length))
    return True

def get_png_dimensions(filename: str) -> tuple[int, int]:
    "Get dimensions from PNG file"
    drum = deque((b'0',)*4, 4)
    with open(filename, 'rb') as png:
        while b''.join(drum) != b'IHDR':#PNG IHDR image header
            byte = png.read(1)
            if byte == b'':
                raise IOError('File does not have a PNG IHDR image header')
            drum.append(byte)
        # PNG integers are big endian / network order
        width = cast(int, struct.unpack('>I', png.read(4))[0])
        height = cast(int, struct.unpack('>I', png.read(4))[0])
    return (width, height)

def unpack_resources(resource_index: str, extract_base_folder: str) -> None:
    "Unpack resource index"
    extract_base_folder = os.path.abspath(extract_base_folder)
    resource_index = os.path.abspath(resource_index)
    folder = os.path.dirname(resource_index)

    items = unpack_index(resource_index)
    files = tuple(cast(str, next(items)) for _ in range(4))
    resource_files = tuple(os.path.join(folder, file) for file in files)

    for metadata in items:
        if isinstance(metadata, str):
            raise ValueError("Metadata is string after already handled files!")
        for rtype in range(2):
            extract_resource(
                rtype, resource_files, metadata, extract_base_folder
            )

def pack_resources(save_folder: str, resource_base_folder: str) -> None:
    "Save modified resource folders into the index and DAT files"
    save_folder = os.path.abspath(save_folder)
    resource_base_folder = os.path.abspath(resource_base_folder)

    metadata = unpack_index(os.path.join(save_folder, 'IconResources.idx'))
    files = tuple(cast(str, next(metadata)) for _ in range(4))

    index = os.path.join(save_folder, 'modified', 'IconResources.idx')
    ensure_path_exists(index)

    for rtype in range(2):
        filename = os.path.join(save_folder, 'modified', files[rtype])
        with open(filename, 'wb') as file:
            file.write(b'fdra')

    def write_png(png_filename: str,
                  length: int,
                  resource_file: io.IOBase) -> int:
        "Write filename PNG file to PSIcons given resource type"
        if not os.path.exists(png_filename):
            return 0
        with open(png_filename, 'rb') as png:
            new_length = cast(int, resource_file.write(png.read()))
        if new_length > length:
            raise MemoryError(f"PNG is greater than {length} bytes long and cannot re-order properly because don't know how to change headers")
        # If less, pad so offsets stay same
        resource_file.write(b'\x00'*(length-new_length))
        return new_length

    def get_metadata(metadata_index: Iterable[ImageMetadata | str]) -> list[ImageMetadata]:
        "Get metadata while updating it and writing PNG files"
        offsets_low: dict[int, int] = {}
        offsets_high: dict[int, int] = {}
        metas: list[ImageMetadata] = []
        for metadata in metadata_index:
            if isinstance(metadata, str):
                raise ValueError("Metadata is string after already handled files!")
            offsets_low[metadata.off_low+0] = len(metas)+0
            offsets_high[metadata.off_high+0] = len(metas)+0
            metas.append(metadata)
        with open(os.path.join(save_folder, 'modified', files[0]), 'wb') as resource:
            for offset in sorted(offsets_low):
                cur_offset = resource.tell()
                resource.write(b'\x00'*(offset-cur_offset))
                if offset == 0:
                    continue
                metadata = metas[offsets_low[offset]]
                png_filename = os.path.join(resource_base_folder, 'Low', f'{metadata.name}.png')
                size = write_png(png_filename, metadata.size_low, resource)
                if size:
                    metadata.set_dimensions(0, get_png_dimensions(png_filename))
                    metadata.set_position(0, (offset, size))

        with open(os.path.join(save_folder, 'modified', files[1]), 'wb') as resource:
            for offset in sorted(offsets_high):
                cur_offset = resource.tell()
                resource.write(b'\x00'*(offset-cur_offset))
                if offset == 0:
                    continue
                metadata = metas[offsets_high[offset]]
                png_filename = os.path.join(resource_base_folder, 'High', f'{metadata.name}.png')
                size = write_png(png_filename, metadata.size_high, resource)
                if size:
                    metadata.set_dimensions(1, get_png_dimensions(png_filename))
                    metadata.set_position(1, (offset, size))
        return metas

    pack_index(
        index,
        (
            'PSIconsLowRes.dat',
            'PSIconsHighRes.dat',
            'PSIconsXLowRes.dat',
            'PSIconsXHighRes.dat'
        ),
        get_metadata(metadata)
    )

def cli_run() -> None:
    "Program command line interface"
    program, *args = sys.argv
    name = os.path.split(program)[1]
    if not args:
        print(f'Usage: {name} {{unpack | pack}} {{ directory, directory }}')
        print('ERROR: no option was provided')
        sys.exit(1)
    modes = ('unpack', 'pack')
    arg_mode, *folders = args
    if arg_mode not in modes:
        print(f'Usage: {name} {{unpack | pack}} {{ directory, directory }}')
        print('ERROR: invalid option provided, must be either unpack or pack')
        sys.exit(1)
    pack = modes.index(arg_mode)# 0 = unpack
    if len(folders) < 2:
        load = ('Resource Index File', 'Save directory')[pack]
        save = ('Extract base directory', 'Resource base directory')[pack]
        print(f'Usage: {name} {arg_mode} {{ {load}, {save} }}')
        print(f'ERROR: missing arguments, must have "{load}" and "{save}" options')
        sys.exit(1)
    folders = [os.path.abspath(os.path.expanduser(f)) for f in folders]
    if pack:
        pack_resources(*folders)
    else:
        unpack_resources(*folders)
    print(f'{arg_mode.title()}ed files successfuly')

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.\n')
    cli_run()
