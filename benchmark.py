from os.path import dirname, join
from json import load
from urllib.parse import urlparse
from time import perf_counter

from ada_url import URL

URL_TEST_DATA_PATH = join(dirname(__file__), 'tests/files/urltestdata.json')

with open(URL_TEST_DATA_PATH, 'rb') as f:
    test_data = load(f)

test_cases = []
for item in test_data:
    if isinstance(item, str) or item.get('failure', False):
        continue
    test_cases.append(item['href'])

print('Function', 'msec', 'URLs/msec', sep='\t')
for func_name, func in (('stdlib urlparse', urlparse), ('ada_url URL', URL)):
    start_time = perf_counter()
    for item in test_cases:
        func(item)
    duration = perf_counter() - start_time
    rate = len(test_cases) / duration
    print(func_name, f'{duration * 1000:0.2f}', f'{rate / 1000:0.2f}', sep='\t')
