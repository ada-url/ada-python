from setuptools import setup

setup(
    cffi_modules=[
        "./what_url/ada_build.py:ffi_builder",
    ],
)
