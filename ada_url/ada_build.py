from cffi import FFI
from os.path import dirname, join
from setuptools.extension import Extension
from sys import platform

file_dir = dirname(__file__)

compile_args = ['/std:c++20'] if platform == 'win32' else ['-std=c++20']

ada_obj = Extension(
    'ada',
    define_macros=[('ADA_INCLUDE_URL_PATTERN', '0')],
    language="c++",
    sources=['ada_url/ada.cpp'],
    include_dirs=[file_dir],
    extra_compile_args=compile_args,
)

libraries = ['stdc++'] if platform == 'linux' else []

ffi_builder = FFI()
ffi_builder.set_source(
    'ada_url._ada_wrapper',
    '# include "ada_c.h"',
    libraries=libraries,
    include_dirs=[file_dir],
    extra_objects=[ada_obj],
)

cdef_lines = []
with open(join(file_dir, 'ada_c.h'), 'rt') as f:
    for line in f:
        if not line.startswith('#'):
            cdef_lines.append(line)
ffi_builder.cdef(''.join(cdef_lines))

if __name__ == '__main__':
    ffi_builder.compile()
