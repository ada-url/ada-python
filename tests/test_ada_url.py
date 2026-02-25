from copy import copy, deepcopy
from json import load
from os.path import dirname, join
from unittest import TestCase

from ada_url import (
    HostType,
    SchemeType,
    URLSearchParams as SearchParams,
    URL,
    check_url,
    get_version,
    idna,
    idna_to_ascii,
    idna_to_unicode,
    join_url,
    normalize_url,
    replace_search_params,
    parse_search_params,
    parse_url,
    replace_url,
)
from ada_url.ada_adapter import GET_ATTRIBUTES

URL_TEST_DATA_PATH = join(dirname(__file__), 'files/urltestdata.json')


class ADAURLTests(TestCase):
    def test_class_get(self):
        url = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        urlobj = URL(url)
        self.assertEqual(
            urlobj.href, 'https://user_1:password_1@example.org:8080/api?q=1#frag'
        )
        self.assertEqual(urlobj.username, 'user_1')
        self.assertEqual(urlobj.password, 'password_1')
        self.assertEqual(urlobj.protocol, 'https:')
        self.assertEqual(urlobj.port, '8080')
        self.assertEqual(urlobj.hostname, 'example.org')
        self.assertEqual(urlobj.host, 'example.org:8080')
        self.assertEqual(urlobj.pathname, '/api')
        self.assertEqual(urlobj.search, '?q=1')
        self.assertEqual(urlobj.hash, '#frag')
        self.assertEqual(urlobj.origin, 'https://example.org:8080')

        with self.assertRaises(AttributeError):
            urlobj.bogus

    def test_class_host_type(self):
        # host_type should return an IntEnum, which can be compared to a Python int
        for url, expected in (
            ('http://localhost:3000', HostType.DEFAULT),
            ('http://0.0.0.0', HostType.IPV4),
            ('http://[2001:db8:3333:4444:5555:6666:7777:8888]', HostType.IPV6),
        ):
            with self.subTest(url=url):
                urlobj = URL(url)
                self.assertEqual(urlobj.host_type, int(expected))
                self.assertEqual(urlobj.host_type, expected)

    def test_class_scheme_type(self):
        # host_type should return an IntEnum, which can be compared to a Python int
        for url, expected in (
            ('http://localhost', SchemeType.HTTP),
            ('git://localhost', SchemeType.NOT_SPECIAL),
            ('https://localhost', SchemeType.HTTPS),
            ('ws://localhost', SchemeType.WS),
            ('ftp://localhost', SchemeType.FTP),
            ('wss://localhost', SchemeType.WSS),
            ('file://localhost', SchemeType.FILE),
        ):
            with self.subTest(url=url):
                urlobj = URL(url)
                self.assertEqual(urlobj.scheme_type, int(expected))
                self.assertEqual(urlobj.scheme_type, expected)

    def test_copy_vs_deepcopy(self):
        obj = URL('http://example.org:8080')
        copied_obj = copy(obj)
        deepcopied_obj = deepcopy(obj)

        obj.port = '8081'
        self.assertEqual(copied_obj.port, '8081')
        self.assertEqual(deepcopied_obj.port, '8080')

        deepcopied_obj.port = '8082'
        self.assertEqual(copied_obj.port, '8081')
        self.assertEqual(deepcopied_obj.port, '8082')

    def test_class_set(self):
        url = 'https://username:password@www.google.com:8080/'
        urlobj = URL(url)
        urlobj.href = 'https://www.yagiz.co'
        urlobj.hash = 'new-hash'
        urlobj.hostname = 'new-host'
        urlobj.host = 'changed-host:9090'
        urlobj.pathname = 'new-pathname'
        urlobj.search = 'new-search'
        urlobj.protocol = 'wss'
        actual = urlobj.href

        with self.assertRaises(ValueError):
            urlobj.hostname = 1

        with self.assertRaises(ValueError):
            urlobj.hostname = '127.0.0.0.0.1'

        expected = 'wss://changed-host:9090/new-pathname?new-search#new-hash'
        self.assertEqual(actual, expected)

    def test_class_delete(self):
        url = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        urlobj = URL(url)

        del urlobj.port
        self.assertEqual(
            urlobj.href, 'https://user_1:password_1@example.org/api?q=1#frag'
        )

        del urlobj.hash
        self.assertEqual(urlobj.href, 'https://user_1:password_1@example.org/api?q=1')

        del urlobj.pathname
        self.assertEqual(urlobj.href, 'https://user_1:password_1@example.org/?q=1')

        del urlobj.search
        self.assertEqual(urlobj.href, 'https://user_1:password_1@example.org/')

        with self.assertRaises(AttributeError):
            del urlobj.href

    def test_unset(self):
        url = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        for attr, expected in (
            ('username', 'https://:password_1@example.org:8080/api?q=1#frag'),
            ('password', 'https://user_1@example.org:8080/api?q=1#frag'),
            ('port', 'https://user_1:password_1@example.org/api?q=1#frag'),
            ('pathname', 'https://user_1:password_1@example.org:8080/?q=1#frag'),
            ('search', 'https://user_1:password_1@example.org:8080/api#frag'),
            ('hash', 'https://user_1:password_1@example.org:8080/api?q=1'),
        ):
            with self.subTest(attr=attr):
                urlobj = URL(url)
                urlobj.__delattr__(attr)
                self.assertEqual(urlobj.href, expected)

    def test_class_with_base(self):
        url = '../example.txt'
        base = 'https://example.org/path/'
        urlobj = URL(url, base)
        self.assertEqual(urlobj.href, 'https://example.org/example.txt')

    def test_class_invalid(self):
        with self.assertRaises(ValueError):
            URL('bogus')

    def test_class_can_parse(self):
        for url, expected in (
            (1, False),
            (None, False),
            ('bogus', False),
            ('https://example.org', True),
        ):
            with self.subTest(url=url):
                actual = URL.can_parse(url)
                self.assertEqual(actual, expected)

    def test_class_can_parse_with_base(self):
        url = 'example.txt'
        for base, expected in (
            ('https://example.org', True),
            (1, False),
            (None, False),
            ('bogus', False),
        ):
            with self.subTest(url=url):
                actual = URL.can_parse(url, base)
                self.assertEqual(actual, expected)

    def test_class_dir(self):
        urlobj = URL('https://example.org')
        actual = set(dir(urlobj))
        self.assertTrue(actual.issuperset(GET_ATTRIBUTES))

    def test_to_str(self):
        urlobj = URL('https://example.org/../something.txt')
        actual = str(urlobj)
        expected = 'https://example.org/something.txt'
        self.assertEqual(actual, expected)

    def test_to_repr(self):
        urlobj = URL('https://example.org/../something.txt')
        actual = repr(urlobj)
        expected = '<URL "https://example.org/something.txt">'
        self.assertEqual(actual, expected)

    def test_to_repr_password(self):
        # Redact the password attribute from __repr__, but keep it on the object.
        urlobj = URL('https://user:password1@example.org/../something.txt')
        self.assertEqual(repr(urlobj), '<URL "https://user@example.org/something.txt">')
        self.assertEqual(urlobj.password, 'password1')
        self.assertEqual(
            str(urlobj), 'https://user:password1@example.org/something.txt'
        )

    def test_check_url(self):
        for s, expected in (
            ('https:example.org', True),
            ('https://////example.com/// ', True),
            ('https://example.com/././foo', True),
            ('file:///C|/demo', True),
            ('https://127.0.0.1./', True),
            ('bogus', False),
            ('https://exa%23mple.org', False),
            ('foo://exa[mple.org', False),
            ('https://127.0.0.0.1./', False),
            (None, False),
            (1, False),
            ('', False),
            ('\n', False),
        ):
            with self.subTest(s=s):
                actual = check_url(s)
                self.assertEqual(actual, expected)

    def test_join_url(self):
        # Tests from https://www.rfc-editor.org/rfc/rfc3986.html
        # sections 5.4.1. and 5.4.2
        base_url = 'http://a/b/c/d;p?q'
        for s, expected in (
            ('g:h', 'g:h'),
            ('g', 'http://a/b/c/g'),
            ('./g', 'http://a/b/c/g'),
            ('g/', 'http://a/b/c/g/'),
            ('/g', 'http://a/g'),
            ('//g', 'http://g/'),  # Slightly different output, trailing /
            ('?y', 'http://a/b/c/d;p?y'),
            ('g?y', 'http://a/b/c/g?y'),
            ('#s', 'http://a/b/c/d;p?q#s'),
            ('g#s', 'http://a/b/c/g#s'),
            ('g?y#s', 'http://a/b/c/g?y#s'),
            (';x', 'http://a/b/c/;x'),
            ('g;x', 'http://a/b/c/g;x'),
            ('g;x?y#s', 'http://a/b/c/g;x?y#s'),
            ('', 'http://a/b/c/d;p?q'),
            ('.', 'http://a/b/c/'),
            ('./', 'http://a/b/c/'),
            ('..', 'http://a/b/'),
            ('../', 'http://a/b/'),
            ('../g', 'http://a/b/g'),
            ('../..', 'http://a/'),
            ('../../', 'http://a/'),
            ('../../g', 'http://a/g'),
            ('/./g', 'http://a/g'),
            ('/../g', 'http://a/g'),
            ('g.', 'http://a/b/c/g.'),
            ('.g', 'http://a/b/c/.g'),
            ('g..', 'http://a/b/c/g..'),
            ('..g', 'http://a/b/c/..g'),
            ('./../g', 'http://a/b/g'),
            ('./g/.', 'http://a/b/c/g/'),
            ('g/./h', 'http://a/b/c/g/h'),
            ('g/../h', 'http://a/b/c/h'),
            ('g;x=1/./y', 'http://a/b/c/g;x=1/y'),
            ('g;x=1/../y', 'http://a/b/c/y'),
            ('g?y/./x', 'http://a/b/c/g?y/./x'),
            ('g?y/../x', 'http://a/b/c/g?y/../x'),
            ('g#s/./x', 'http://a/b/c/g#s/./x'),
            ('g#s/../x', 'http://a/b/c/g#s/../x'),
        ):
            with self.subTest(s=s):
                actual = join_url(base_url, s)
                self.assertEqual(actual, expected)

    def test_join_url_invalid(self):
        for base_url, s in (
            (1, './g'),
            ('https://example.org', 1),
            ('bogus', './g'),
        ):
            with self.subTest(base_url=base_url, s=s):
                with self.assertRaises(ValueError):
                    join_url(base_url, s)

    def test_normalize_url(self):
        for s, expected in (
            ('https://example.org', 'https://example.org/'),
            ('https://example.org/../yolo.txt', 'https://example.org/yolo.txt'),
            ('https://example.org/dir/../yolo.txt', 'https://example.org/yolo.txt'),
            (
                'https://example.org/dir_1/dir_2/../../yolo.txt',
                'https://example.org/yolo.txt',
            ),
            (
                'https://example.org/dir_1/dir_2/../../../yolo.txt',
                'https://example.org/yolo.txt',
            ),
            (
                'https://example.org/dir_1/dir_2/../..//yolo.txt',
                'https://example.org//yolo.txt',
            ),
        ):
            with self.subTest(s=s):
                actual = normalize_url(s)
                self.assertEqual(actual, expected)

    def test_normalize_url_error(self):
        for s in (1, 'bogus'):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):
                    normalize_url(s)

    def test_parse_url(self):
        s = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        actual = parse_url(s)
        expected = {
            'href': 'https://user_1:password_1@example.org:8080/api?q=1#frag',
            'username': 'user_1',
            'password': 'password_1',
            'protocol': 'https:',
            'host': 'example.org:8080',
            'port': '8080',
            'hostname': 'example.org',
            'pathname': '/api',
            'search': '?q=1',
            'hash': '#frag',
            'origin': 'https://example.org:8080',
            'host_type': HostType(0),
            'scheme_type': SchemeType(2),
        }
        self.assertEqual(actual, expected)

    def test_parse_url_subset(self):
        s = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        actual = parse_url(s, attributes=('username', 'password'))
        expected = {'username': 'user_1', 'password': 'password_1'}
        self.assertEqual(actual, expected)

    def test_parse_url_error(self):
        for s in (1, 'bogus'):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):
                    parse_url(s)

    def test_replace_url(self):
        s = 'https://www.example.org/yolo.txt?q=1#2'
        for kwargs, expected in (
            (
                {'username': 'user', 'password': 'pass'},
                'https://user:pass@www.example.org/yolo.txt?q=1#2',
            ),
            ({'protocol': 'http:'}, 'http://www.example.org/yolo.txt?q=1#2'),
            ({'protocol': 'http'}, 'http://www.example.org/yolo.txt?q=1#2'),
            ({'port': '80'}, 'https://www.example.org:80/yolo.txt?q=1#2'),
            ({'host': 'www.example.com'}, 'https://www.example.com/yolo.txt?q=1#2'),
            ({'hostname': 'example.com'}, 'https://example.com/yolo.txt?q=1#2'),
            ({'search': '?q=0'}, 'https://www.example.org/yolo.txt?q=0#2'),
            ({'hash': '0'}, 'https://www.example.org/yolo.txt?q=1#0'),
        ):
            with self.subTest(kwargs=kwargs):
                actual = replace_url(s, **kwargs)
                self.assertEqual(actual, expected)

    def test_replace_url_clear(self):
        s = 'https://user_1:password_1@example.org:8443/api?q=1#frag'
        actual = replace_url(s, port='', hash='', search='')
        expected = 'https://user_1:password_1@example.org/api'
        self.assertEqual(actual, expected)

    def test_replace_url_unset(self):
        s = 'https://user:pass@example.org'
        actual = replace_url(s, username='', password='')
        expected = 'https://example.org/'
        self.assertEqual(actual, expected)

    def test_replace_href(self):
        s = 'https://username:password@www.google.com:8080/'
        kwargs = {
            'href': 'https://www.yagiz.co',
            'hash': 'new-hash',
            'hostname': 'new-host',
            'host': 'changed-host:9090',
            'pathname': 'new-pathname',
            'search': 'new-search',
            'protocol': 'wss',
        }
        actual = replace_url(s, **kwargs)
        expected = 'wss://changed-host:9090/new-pathname?new-search#new-hash'
        self.assertEqual(actual, expected)

    def test_replace_url_error(self):
        for s, kwargs in (
            (1, {}),
            ('bogus', {}),
            ('http://localhost/', {'password': 1}),
            ('http://localhost/', {'hostname': 'exa[mple.org'}),
        ):
            with self.subTest(s=s, kwargs=kwargs):
                with self.assertRaises(ValueError):
                    replace_url(s, **kwargs)

    def test_idna_decode(self):
        self.assertEqual(idna.decode('xn--meagefactory-m9a.ca'), 'meßagefactory.ca')
        self.assertEqual(
            idna_to_unicode(b'xn--meagefactory-m9a.ca'), 'meßagefactory.ca'
        )

    def test_idna_encode(self):
        self.assertEqual(idna.encode('meßagefactory.ca'), b'xn--meagefactory-m9a.ca')
        self.assertEqual(
            idna_to_ascii('meßagefactory.ca'.encode('utf-8')),
            b'xn--meagefactory-m9a.ca',
        )


class SearchParamsTests(TestCase):
    def test_append(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        search_params.append('key2', 'value4')
        search_params.append('key3', 'value5')
        actual = list(search_params.items())
        expected = [
            ('key1', 'value1'),
            ('key1', 'value2'),
            ('key2', 'value3'),
            ('key2', 'value4'),
            ('key3', 'value5'),
        ]
        self.assertEqual(actual, expected)

    def test_delete_key(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        search_params.delete('key1')
        search_params.delete('key3')
        actual = list(search_params.items())
        expected = [('key2', 'value3')]
        self.assertEqual(actual, expected)

    def test_delete_value(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        search_params.delete('key1', 'value1')
        search_params.delete('key1', 'value4')
        search_params.delete('key3', 'value5')
        actual = list(search_params.items())
        expected = [('key1', 'value2'), ('key2', 'value3')]
        self.assertEqual(actual, expected)

    def test_get(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        self.assertEqual(search_params.get('key1'), 'value1')
        self.assertEqual(search_params.get('key2'), 'value3')
        self.assertEqual(search_params.get('key3'), '')

    def test_get_all(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        self.assertEqual(search_params.get_all('key1'), ['value1', 'value2'])
        self.assertEqual(search_params.get_all('key2'), ['value3'])

    def test_has_key(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        self.assertTrue(search_params.has('key1'))
        self.assertTrue(search_params.has('key2'))
        self.assertFalse(search_params.has('key3'))

    def test_has_value(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        self.assertTrue(search_params.has('key1', 'value1'))
        self.assertTrue(search_params.has('key1', 'value2'))
        self.assertTrue(search_params.has('key2', 'value3'))
        self.assertFalse(search_params.has('key1', 'value4'))
        self.assertFalse(search_params.has('key2', 'value5'))
        self.assertFalse(search_params.has('key3', 'value6'))

    def test_items(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        actual = list(search_params.items())
        expected = [('key1', 'value1'), ('key1', 'value2'), ('key2', 'value3')]
        self.assertEqual(actual, expected)

    def test_size(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        self.assertEqual(search_params.size, 3)

    def test_keys(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        actual = list(search_params.keys())
        expected = ['key1', 'key1', 'key2']
        self.assertEqual(actual, expected)

    def test_repr(self):
        search_params = SearchParams('key1=value1')
        actual = repr(search_params)
        expected = '<SearchParams "key1=value1">'
        self.assertEqual(actual, expected)

    def test_set(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        search_params.set('key1', 'value4')
        search_params.set('key3', 'value5')
        actual = list(search_params.items())
        expected = [('key1', 'value4'), ('key2', 'value3'), ('key3', 'value5')]
        self.assertEqual(actual, expected)

    def test_sort(self):
        search_params = SearchParams('key2=value2&key1=value1&key3=value3')
        search_params.sort()
        actual = list(search_params.items())
        expected = [('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')]
        self.assertEqual(actual, expected)

    def test_str(self):
        params = 'key2=value2&key1=value1&key3=value3'
        search_params = SearchParams(params)
        self.assertEqual(str(search_params), params)

    def test_values(self):
        search_params = SearchParams('key1=value1&key1=value2&key2=value3')
        actual = list(search_params.values())
        expected = ['value1', 'value2', 'value3']
        self.assertEqual(actual, expected)

    def test_parse_search_params(self):
        s = 'key1=value1&key1=value2&key2=value3'
        actual = parse_search_params(s)
        expected = {'key1': ['value1', 'value2'], 'key2': ['value3']}
        self.assertEqual(actual, expected)

    def test_replace_search_params(self):
        s = 'key1=value1&key1=value2&key2=value3'
        actual = replace_search_params(s, ('key1', 'value4'), ('key1', 'value5'))
        expected = 'key2=value3&key1=value4&key1=value5'
        self.assertEqual(actual, expected)


class ParseTests(TestCase):
    def test_url_suite(self):
        with open(URL_TEST_DATA_PATH, 'rb') as f:
            test_data = load(f)

        for i, item in enumerate(test_data, 1):
            # Skip the comments
            if isinstance(item, str):
                continue

            # Skip tests that can't be represented properly with the json module
            try:
                (item.get('input') or '').encode('utf-8')
                (item.get('base') or '').encode('utf-8')
            except UnicodeEncodeError:
                continue

            with self.subTest(i=i):
                s = item['input']
                base = item.get('base', None)
                if item.get('failure', False):
                    with self.assertRaises(ValueError):
                        URL(s, base=base)
                else:
                    urlobj = URL(s, base=base)
                    self.assertEqual(urlobj.href, item['href'])


class GetVersionTests(TestCase):
    def test_get_version(self):
        value = get_version()
        version_parts = value.split('.')
        self.assertEqual(len(version_parts), 3)  # Three parts
        int(version_parts[0])  # Major should be an integer
        int(version_parts[1])  # Minor should be an integer
