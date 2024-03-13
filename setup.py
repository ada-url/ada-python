from setuptools import setup

setup(
    cffi_modules=[
        './ada_url/ada_build.py:ffi_builder',
    ],
)
