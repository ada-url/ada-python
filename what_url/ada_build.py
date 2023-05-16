from cffi import FFI
from os.path import dirname, join
from sys import platform

file_dir = dirname(__file__)

libraries = ['stdc++'] if platform == 'linux' else []

ffi_builder = FFI()
ffi_builder.set_source(
    'what_url._ada_wrapper',
    '# include "ada_c.h"',
    include_dirs=[file_dir],
    libraries=libraries,
    extra_objects=[join(file_dir, 'ada.o')],
)

cdef_lines = []
with open(join(file_dir, 'ada_c.h'), 'rt') as f:
    for line in f:
        if not line.startswith('#'):
            cdef_lines.append(line)
ffi_builder.cdef(''.join(cdef_lines))

if __name__ == '__main__':
    ffi_builder.compile()
