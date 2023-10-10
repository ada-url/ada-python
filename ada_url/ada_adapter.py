from enum import IntEnum
from typing import Final, Iterable, Iterator, List, Optional, TypedDict, Union

from ada_url._ada_wrapper import ffi, lib

URL_ATTRIBUTES = (
    'href',
    'username',
    'password',
    'protocol',
    'port',
    'hostname',
    'host',
    'pathname',
    'search',
    'hash',
)
PARSE_ATTRIBUTES = URL_ATTRIBUTES + ('origin', 'host_type', 'scheme_type')

# These are the attributes that have corresponding ada_get_* functions
GET_ATTRIBUTES = frozenset(PARSE_ATTRIBUTES)

# These are the attributes that have corresponding ada_set_* functons
SET_ATTRIBUTES = frozenset(URL_ATTRIBUTES)

# These are the attributes that can be cleared with one of the ada_clear_* functions
CLEAR_ATTRIBUTES = frozenset(('port', 'hash', 'search'))

# These are the attributes that must be cleared by setting the empty string
UNSET_ATTRIBUTES = frozenset(('username', 'password', 'pathname'))

_marker = object()


class HostType(IntEnum):
    """
    Enum for URL host types:

    * ``DEFAULT`` hosts like ``https://example.org`` are ``0``.
    * ``IPV4`` hosts like ``https://192.0.2.1`` are ``1``.
    * ``IPV6`` hosts like ``https://[2001:db8::]`` are ``2``.

    .. code-block:: python

        >>> from ada_url import HostType
        >>> HostType.DEFAULT
        <HostType.DEFAULT: 0>

    """

    DEFAULT = 0
    IPV4 = 1
    IPV6 = 2


class SchemeType(IntEnum):
    """
    Enum for `URL scheme types <https://url.spec.whatwg.org/#url-miscellaneous>`__.

    * ``HTTP`` URLs like ``http://example.org`` are ``0``.
    * ``NOT_SPECIAL`` URLs like ``git://example.og`` are ``1``.
    * ``HTTPS`` URLs like ``https://example.org`` are ``2``.
    * ``WS`` URLs like ``ws://example.org`` are ``3``.
    * ``FTP`` URLs like ``ftp://example.org`` are ``4``.
    * ``WSS`` URLs like ``wss://example.org`` are ``5``.
    * ``FILE`` URLs like ``file://example`` are ``6``.

    .. code-block:: python

        >>> from ada_url import SchemeType
        >>> SchemeType.HTTPS
        <SchemeType.HTTPS: 2>

    """

    HTTP = 0
    NOT_SPECIAL = 1
    HTTPS = 2
    WS = 3
    FTP = 4
    WSS = 5
    FILE = 6


class ParseAttributes(TypedDict, total=False):
    href: str
    username: str
    password: str
    protocol: str
    port: str
    hostname: str
    host: str
    pathname: str
    search: str
    hash: str
    origin: str
    host_type: HostType
    scheme_type: SchemeType


def _get_obj(constructor, destructor, *args):
    obj = constructor(*args)

    return ffi.gc(obj, destructor)


def _get_str(x):
    ret = ffi.string(x.data, x.length).decode('utf-8') if x.length else ''
    return ret


class URL:
    """
    Parses a *url* (with an optional *base*) according to the
    WHATWG URL parsing standard.

    .. code-block:: python

        >>> from ada_url import URL
        >>> old_url = 'https://example.org:443/file.txt?q=1'
        >>> urlobj = URL(old_url)
        >>> urlobj.host
        'example.org'
        >>> urlobj.host = 'example.com'
        >>> new_url = urlobj.href
        >>> new_url
        'https://example.com:443/file.txt?q=1'

    You can read and write the following attributes:

    * ``href``
    * ``protocol``
    * ``username``
    * ``password``
    * ``host``
    * ``hostname``
    * ``port``
    * ``pathname``
    * ``search``
    * ``hash``

    You can additionally read these attributes:

    * ``origin``, which will be a ``str``
    * ``host_type``, which will be a :class:`HostType` enum
    * ``scheme_type``, which will be a :class:`SchemeType` enum

    The class also exposes a static method that checks whether the input
    *url* (and optional *base*) can be parsed:

    .. code-block:: python

        >>> url = 'file_2.txt'
        >>> base = 'https://example.org:443/file_1.txt'
        >>> URL.can_parse(url, base)
        True

    See the `WHATWG docs <https://url.spec.whatwg.org/#url-class>`__ for
    more details on the URL class.

    """

    href: str
    username: str
    password: str
    protocol: str
    port: str
    hostname: str
    host: str
    pathname: str
    search: str
    hash: str
    origin: Final[str]
    host_type: Final[HostType]
    scheme_type: Final[SchemeType]

    def __init__(self, url: str, base: Optional[str] = None):
        url_bytes = url.encode('utf-8')

        if base is None:
            self.urlobj = _get_obj(
                lib.ada_parse, lib.ada_free, url_bytes, len(url_bytes)
            )
        else:
            base_bytes = base.encode('utf-8')
            self.urlobj = _get_obj(
                lib.ada_parse_with_base,
                lib.ada_free,
                url_bytes,
                len(url_bytes),
                base_bytes,
                len(base_bytes),
            )

        if not lib.ada_is_valid(self.urlobj):
            raise ValueError('Invalid input')

    def __copy__(self):
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        super(URL, ret).__init__()
        return ret

    def __deepcopy__(self, memo):
        cls = self.__class__
        ret = cls.__new__(cls)
        super(URL, ret).__init__()
        ret.urlobj = lib.ada_copy(self.urlobj)

        return ret

    def __delattr__(self, attr: str):
        if attr in CLEAR_ATTRIBUTES:
            clear_func = getattr(lib, f'ada_clear_{attr}')
            clear_func(self.urlobj)
        elif attr in UNSET_ATTRIBUTES:
            set_func = getattr(lib, f'ada_set_{attr}')
            set_func(self.urlobj, b'', 0)
        else:
            raise AttributeError(f'cannot remove {attr}')

    def __dir__(self) -> List[str]:
        return super().__dir__() + list(PARSE_ATTRIBUTES)

    def __getattr__(self, attr: str) -> Union[str, HostType, SchemeType]:
        if attr in GET_ATTRIBUTES:
            get_func = getattr(lib, f'ada_get_{attr}')
            data = get_func(self.urlobj)
            if attr == 'origin':
                ret = _get_str(data)
                lib.ada_free_owned_string(data)
            elif attr == 'host_type':
                ret = HostType(data)
            elif attr == 'scheme_type':
                ret = SchemeType(data)
            else:
                ret = _get_str(data)

            return ret

        raise AttributeError(f'no attribute named {attr}')

    def __setattr__(self, attr: str, value: str) -> None:
        if attr in SET_ATTRIBUTES:
            try:
                value_bytes = value.encode('utf-8')
            except Exception:
                raise ValueError(f'Invalid value for {attr}') from None

            set_func = getattr(lib, f'ada_set_{attr}')
            ret = set_func(self.urlobj, value_bytes, len(value_bytes))
            if (ret is not None) and (not ret):
                raise ValueError(f'Invalid value for {attr}') from None

            return ret

        return super().__setattr__(attr, value)

    def __str__(self):
        return self.href

    def __repr__(self):
        return f'<URL "{self.href}">'

    @staticmethod
    def can_parse(url: str, base: Optional[str] = None) -> bool:
        try:
            url_bytes = url.encode('utf-8')
        except Exception:
            return False

        if base is None:
            return lib.ada_can_parse(url_bytes, len(url_bytes))

        try:
            base_bytes = base.encode('utf-8')
        except Exception:
            return False

        return lib.ada_can_parse_with_base(
            url_bytes, len(url_bytes), base_bytes, len(base_bytes)
        )


class URLSearchParams:
    """
    Parses the given *params* string according to the WHATWG URL parsing standard.

    The attribute and methods from the standard are implemented:

    .. code-block:: python

        >>> from ada_url import URLSearchParams
        >>> obj = URLSearchParams('key1=value1&key2=value2&key2=value3')
        >>> obj.size
        3
        >>> obj.append('key2', 'value4')
        >>> str(obj)
        'key1=value1&key2=value2&key2=value3&key2=value4'
        >>> obj.delete('key1')
        >>> str(obj)
        'key2=value2&key2=value3&key2=value4'
        >>> obj.delete('key2', 'value2')
        >>> str(obj)
        'key2=value3&key2=value4'
        >>> obj.get('key2')
        'value3'
        >>> obj.get_all('key2')
        ['value3', 'value4']
        >>> obj.has('key2')
        True
        >>> obj.has('key2', 'value5')
        False
        >>> obj.set('key1', 'value6')
        >>> str(obj)
        'key2=value3&key2=value4&key1=value6'
        >>> obj.sort()
        >>> str(obj)
        'key1=value6&key2=value3&key2=value4'

    Iterators for the ``keys``, ``values``, and ``items`` are also implemented:

    .. code-block:: python

        >>> obj = URLSearchParams('key1=value1&key2=value2&key2=value3')
        >>> list(obj.keys())
        ['key1', 'key2', 'key2']
        >>> list(obj.values())
        ['value1', 'value2', 'value3']
        >>> list(obj.items())
        [('key1', 'value1'), ('key2', 'value2'), ('key2', 'value3')]

    See the `WHATWG docs <https://url.spec.whatwg.org/#interface-urlsearchparams>`__ for
    more details on the URLSearchParams class.

    """

    def __init__(self, params: str):
        params_bytes = params.encode('utf-8')
        self.paramsobj = _get_obj(
            lib.ada_parse_search_params,
            lib.ada_free_search_params,
            params_bytes,
            len(params_bytes),
        )

    @property
    def size(self) -> int:
        return lib.ada_search_params_size(self.paramsobj)

    def append(self, key: str, value: str):
        key_bytes = key.encode('utf-8')
        value_bytes = value.encode('utf-8')
        lib.ada_search_params_append(
            self.paramsobj,
            key_bytes,
            len(key_bytes),
            value_bytes,
            len(value_bytes),
        )

    def delete(self, key: str, value: Optional[str] = None):
        key_bytes = key.encode('utf-8')
        if value is None:
            lib.ada_search_params_remove(self.paramsobj, key_bytes, len(key_bytes))
        else:
            value_bytes = value.encode('utf-8')
            lib.ada_search_params_remove_value(
                self.paramsobj,
                key_bytes,
                len(key_bytes),
                value_bytes,
                len(value_bytes),
            )

    def get(self, key: str) -> str:
        key_bytes = key.encode('utf-8')
        item = lib.ada_search_params_get(self.paramsobj, key_bytes, len(key_bytes))
        return _get_str(item)

    def get_all(self, key: str) -> list[str]:
        key_bytes = key.encode('utf-8')
        items = lib.ada_search_params_get_all(self.paramsobj, key_bytes, len(key_bytes))
        count = lib.ada_strings_size(items)

        ret = []
        for i in range(count):
            value = _get_str(lib.ada_strings_get(items, i))
            ret.append(value)

        return ret

    def has(self, key: str, value: Optional[str] = None) -> bool:
        key_bytes = key.encode('utf-8')
        if value is None:
            return lib.ada_search_params_has(self.paramsobj, key_bytes, len(key_bytes))
        else:
            value_bytes = value.encode('utf-8')
            return lib.ada_search_params_has_value(
                self.paramsobj,
                key_bytes,
                len(key_bytes),
                value_bytes,
                len(value_bytes),
            )

    def set(self, key: str, value: str):
        key_bytes = key.encode('utf-8')
        value_bytes = value.encode('utf-8')
        lib.ada_search_params_set(
            self.paramsobj,
            key_bytes,
            len(key_bytes),
            value_bytes,
            len(value_bytes),
        )

    def sort(self):
        lib.ada_search_params_sort(self.paramsobj)

    def keys(self) -> Iterator[str]:
        iterator = _get_obj(
            lib.ada_search_params_get_keys,
            lib.ada_free_search_params_keys_iter,
            self.paramsobj,
        )
        while lib.ada_search_params_keys_iter_has_next(iterator):
            item = lib.ada_search_params_keys_iter_next(iterator)
            yield _get_str(item)

    def values(self) -> Iterator[str]:
        iterator = _get_obj(
            lib.ada_search_params_get_values,
            lib.ada_free_search_params_values_iter,
            self.paramsobj,
        )
        while lib.ada_search_params_values_iter_has_next(iterator):
            item = lib.ada_search_params_values_iter_next(iterator)
            yield _get_str(item)

    def items(self) -> Iterator[tuple[str, str]]:
        iterator = _get_obj(
            lib.ada_search_params_get_entries,
            lib.ada_free_search_params_entries_iter,
            self.paramsobj,
        )
        while lib.ada_search_params_entries_iter_has_next(iterator):
            item = lib.ada_search_params_entries_iter_next(iterator)
            yield _get_str(item.key), _get_str(item.value)

    def __repr__(self):
        return f'<SearchParams "{self}">'

    def __str__(self) -> str:
        result = _get_obj(
            lib.ada_search_params_to_string, lib.ada_free_owned_string, self.paramsobj
        )
        return _get_str(result)


def check_url(s: str) -> bool:
    """
    Returns ``True`` if *s* represents a valid URL, and ``False`` otherwise.

    .. code-block:: python

        >>> from ada_url import check_url
        >>> check_url('bogus')
        False
        >>> check_url('http://a/b/c/d;p?q')
        True

    """
    try:
        s_bytes = s.encode('utf-8')
    except Exception:
        return False

    urlobj = _get_obj(lib.ada_parse, lib.ada_free, s_bytes, len(s_bytes))
    return lib.ada_is_valid(urlobj)


def join_url(base_url: str, s: str) -> str:
    """
    Return the URL that results from joining *base_url* to *s*.
    Raises ``ValueError`` if no valid URL can be constructed.

    .. code-block:: python

        >>> from ada_url import join_url
        >>> base_url = 'http://a/b/c/d;p?q'
        >>> join_url(base_url, '../g')
        'http://a/b/g'

    """
    try:
        base_bytes = base_url.encode('utf-8')
        s_bytes = s.encode('utf-8')
    except Exception:
        raise ValueError('Invalid URL') from None

    urlobj = _get_obj(
        lib.ada_parse_with_base,
        lib.ada_free,
        s_bytes,
        len(s_bytes),
        base_bytes,
        len(base_bytes),
    )
    if not lib.ada_is_valid(urlobj):
        raise ValueError('Invalid URL') from None

    return _get_str(lib.ada_get_href(urlobj))


def normalize_url(s: str) -> str:
    """
    Returns a "normalized" URL with all ``'..'`` and ``'/'`` characters resolved.

    .. code-block:: python

        >>> from ada_url import normalize_url
        >>> normalize_url('http://a/b/c/../g')
        'http://a/b/g'

    """
    return parse_url(s, attributes=('href',))['href']


def parse_url(s: str, attributes: Iterable[str] = PARSE_ATTRIBUTES) -> ParseAttributes:
    """
    Returns a dictionary with the parsed components of the URL represented by *s*.

    .. code-block:: python

        >>> from ada_url import parse_url
        >>> url = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        >>> parse_url(url)
        {
            'href': 'https://user_1:password_1@example.org:8080/api?q=1#frag',
            'username': 'user_1',
            'password': 'password_1',
            'protocol': 'https:',
            'host': 'example.org:8080',
            'port': '8080',
            'hostname': 'example.org',
            'pathname': '/api',
            'search': '?q=1',
            'hash': '#frag'
            'origin': 'https://example.org:8080',
            'host_type': 0
            'scheme_type': 2
        }

    The names of the dictionary keys correspond to the components of the "URL class"
    in the WHATWG URL spec.
    ``host_type`` is a :class:`HostType` enum.
    ``scheme_type`` is a :class:`SchemeType` enum.

    Pass in a sequence of *attributes* to limit which keys are returned.

    .. code-block:: python

        >>> from ada_url import parse_url
        >>> url = 'https://user_1:password_1@example.org:8080/dir/../api?q=1#frag'
        >>> parse_url(url, attributes=('protocol'))
        {'protocol': 'https:'}

    Unrecognized attributes are ignored.

    """
    try:
        s_bytes = s.encode('utf-8')
    except Exception:
        raise ValueError('Invalid URL') from None

    ret = {}
    urlobj = _get_obj(lib.ada_parse, lib.ada_free, s_bytes, len(s_bytes))
    if not lib.ada_is_valid(urlobj):
        raise ValueError('Invalid URL') from None

    for attr in attributes:
        get_func = getattr(lib, f'ada_get_{attr}')
        data = get_func(urlobj)
        if attr == 'origin':
            ret[attr] = _get_str(data)
            lib.ada_free_owned_string(data)
        elif attr == 'host_type':
            ret[attr] = HostType(data)
        elif attr == 'scheme_type':
            ret[attr] = SchemeType(data)
        else:
            ret[attr] = _get_str(data)

    return ret


def replace_url(s: str, **kwargs: str) -> str:
    """
    Start with the URL represented by *s*, replace the attributes given in the *kwargs*
    mapping, and return a normalized URL with the result.

    Provide an empty string to unset an attribute.

    .. code-block:: python

        >>> from ada_url import replace_url
        >>> base_url = 'https://user_1:password_1@example.org/resource'
        >>> replace_url(base_url, username='user_2', password='', protocol='http:')
        'http://user_2@example.org/resource'

    Unrecognized attributes are ignored. ``href`` is replaced first if it is given.
    ``hostname`` is replaced before ``host`` if both are given.

    ``ValueError`` is raised if the input URL or one of the components is not valid.
    """
    try:
        s_bytes = s.encode('utf-8')
    except Exception:
        raise ValueError('Invalid URL') from None

    urlobj = _get_obj(lib.ada_parse, lib.ada_free, s_bytes, len(s_bytes))
    if not lib.ada_is_valid(urlobj):
        raise ValueError('Invalid URL') from None

    # We process attributes in the order given by the documentation, e.g.
    # href before anything else.
    for attr in URL_ATTRIBUTES:
        value = kwargs.get(attr, _marker)
        if value is _marker:
            continue

        try:
            value_bytes = value.encode('utf-8')
        except Exception:
            raise ValueError(f'Invalid value for {attr}') from None

        if (not value_bytes) and (attr in CLEAR_ATTRIBUTES):
            clear_func = getattr(lib, f'ada_clear_{attr}')
            clear_func(urlobj)
        else:
            set_func = getattr(lib, f'ada_set_{attr}')
            set_result = set_func(urlobj, value_bytes, len(value_bytes))
            if (set_result is not None) and (not set_result):
                raise ValueError(f'Invalid value for {attr}') from None

    return _get_str(lib.ada_get_href(urlobj))


def parse_search_params(s: str) -> dict:
    """
    Returns a dictionary representing the parsed URL Parameters specified by *s*.
    The returned dictionary maps each key to a list of values associated with it.

    .. code-block:: python

        >>> from ada_url import parse_search_params
        >>> parse_search_params('key1=value1&key1=value2&key2=value3')
        {'key1': ['value1', 'value2'], 'key2': ['value3']}

    """
    ret = {}
    for key, value in URLSearchParams(s).items():
        if key not in ret:
            ret[key] = [value]
        else:
            ret[key].append(value)

    return ret


def replace_search_params(s: str, *args: tuple[str, str]) -> str:
    """
    Returns a string representing the URL parameters specified by *s*, modified by the
    ``(key, value)`` pairs passed in as *args*.

    .. code-block:: python

        >>> from ada_url import replace_search_params
        >>> replace_search_params(
        ...     'key1=value1&key1=value2',
        ...     ('key1', 'value3'),
        ...     ('key2', 'value4')
        ... )
        'key1=value3&key2=value4'
    """
    search_params = URLSearchParams(s)
    for key, value in args:
        search_params.delete(key)

    for key, value in args:
        search_params.append(key, value)

    return str(search_params)


class idna:
    """Process international domains according to the UTS #46 standard.

    :func:`idna.encode` implements the UTS #46 ``ToASCII`` operation.
    Its output is a Python ``bytes`` object.
    It is also available as :func:`idna_to_ascii`.

    .. code-block:: python

        >>> from ada_url import idna
        >>> idna.encode('meßagefactory.ca')
        b'xn--meagefactory-m9a.ca'

    :func:`idna.decode` implements the UTS #46 ``ToUnicode`` operation.
    Its oputput is a Python ``str`` object.
    It is also available as :func:`idna_to_unicode`.

    .. code-block:: python

        >>> from ada_url import idna
        >>> idna.decode('xn--meagefactory-m9a.ca')
        'meßagefactory.ca'

    Both functions accept either ``str`` or ``bytes`` objects as input.
    """

    @staticmethod
    def decode(s: Union[str, bytes]) -> str:
        if isinstance(s, str):
            s = s.encode('ascii')

        data = _get_obj(lib.ada_idna_to_unicode, lib.ada_free_owned_string, s, len(s))
        return _get_str(data)

    @staticmethod
    def encode(s: Union[str, bytes]) -> str:
        if isinstance(s, str):
            s = s.encode('utf-8')

        val = _get_obj(lib.ada_idna_to_ascii, lib.ada_free_owned_string, s, len(s))
        return ffi.string(val.data, val.length) if val.length else b''


idna_to_unicode = idna.decode

idna_to_ascii = idna.encode
