"""
update_sdist.py

Run this script to remove compiled artifacts from source distribution tarballs.
"""

from pathlib import Path
from tarfile import open as tar_open
from tempfile import TemporaryDirectory

REMOVE_FILES = frozenset(['ada_url/ada.o'])


def update_archive(file_path, removals):
    with TemporaryDirectory() as temp_dir:
        with tar_open(file_path, mode='r:gz') as tf:
            tf.extractall(temp_dir)

        dir_path = next(Path(temp_dir).glob('ada_url-*'))
        all_files = []
        for file_path in Path(temp_dir).glob('**/*'):
            if file_path.is_dir():
                continue
            if str(file_path.relative_to(dir_path)) in REMOVE_FILES:
                continue
            all_files.append(file_path)

        with tar_open(file_path, mode='w:gz') as tf:
            for file_path in all_files:
                arcname = file_path.relative_to(temp_dir)
                print(arcname)
                tf.add(file_path, arcname=arcname)


if __name__ == '__main__':
    for file_path in Path().glob('dist/*.tar.gz'):
        update_archive(file_path, REMOVE_FILES)
        print(f'Updated {file_path}')
