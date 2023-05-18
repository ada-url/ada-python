import os
import shutil
import sys

# Put the project package on the path
parent_dir = os.path.abspath('..')
sys.path.insert(0, parent_dir)

# Copy README.rst so it can be included in index.rst
build_dir = '_build'
os.makedirs(build_dir, exist_ok=True)

readme_src = os.path.join(parent_dir, 'README.rst')
readme_dst = os.path.join(build_dir, 'README.pprst')
shutil.copyfile(readme_src, readme_dst)

project = 'ada-url/ada-python '
copyright = '2023, Ada authors'
author = 'Ada authors'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
autodoc_member_order = 'bysource'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
