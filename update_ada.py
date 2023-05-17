"""
update_ada.py

Run this script to pull in the latest version of `ada-url/ada` single
header package.
"""
from io import BytesIO
from os.path import dirname, join
from zipfile import ZipFile

from certifi import where
from urllib3 import PoolManager


RELEASE_URL = 'https://github.com/ada-url/ada/releases/latest/download/singleheader.zip'
TARGET_DIR = join(dirname(__file__), 'ada_url/')


def main():
    http_client = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=where())
    resp = http_client.request('GET', RELEASE_URL)
    with BytesIO(resp.data) as f, ZipFile(f) as z:
        for file_name in ('ada.cpp', 'ada.h', 'ada_c.h'):
            z.extract(file_name, TARGET_DIR)


if __name__ == '__main__':
    main()
