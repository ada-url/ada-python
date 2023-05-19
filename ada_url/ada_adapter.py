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
PARSE_ATTRIBUTES = URL_ATTRIBUTES + ('origin',)

GET_ATTRIBUTES = frozenset(PARSE_ATTRIBUTES)
SET_ATTRIBUTES = frozenset(URL_ATTRIBUTES)


def _get_urlobj(constructor, *args):
    urlobj = constructor(*args)

    return ffi.gc(urlobj, lib.ada_free)


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

    You can additionally read the ``origin`` attribute.

    The class also exposes a static method that checks whether the input
    *url* (and optional *base*) can be parsed:

    .. code-block:: python

        >>> url = 'https://example.org:443/file_1.txt'
        >>> base = 'file_2.txt'
        >>> URL.can_parse(url, base)
        True

    See the `WHATWG docs <https://url.spec.whatwg.org/#url-class>`__ for
    more details on the URL class.

    """

    def __init__(self, url, base=None):
        url_bytes = url.encode('utf-8')

        if base is None:
            self.urlobj = _get_urlobj(lib.ada_parse, url_bytes, len(url_bytes))
        else:
            base_bytes = base.encode('utf-8')
            self.urlobj = _get_urlobj(
                lib.ada_parse_with_base,
                url_bytes,
                len(url_bytes),
                base_bytes,
                len(base_bytes),
            )

        if not lib.ada_is_valid(self.urlobj):
            raise ValueError('Invalid input')

    def __dir__(self):
        return super().__dir__() + list(PARSE_ATTRIBUTES)

    def __getattr__(self, attr):
        if attr in GET_ATTRIBUTES:
            get_func = getattr(lib, f'ada_get_{attr}')
            data = get_func(self.urlobj)
            ret = _get_str(data)
            if attr == 'origin':
                lib.ada_free_owned_string(data)

            return ret

        return super().__getattr__(self, attr)

    def __setattr__(self, attr, value):
        if attr in SET_ATTRIBUTES:
            try:
                value_bytes = value.encode()
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
    def can_parse(url, base=None):
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


def check_url(s):
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

    urlobj = _get_urlobj(lib.ada_parse, s_bytes, len(s_bytes))
    return lib.ada_is_valid(urlobj)


def join_url(base_url, s):
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

    urlobj = _get_urlobj(
        lib.ada_parse_with_base, s_bytes, len(s_bytes), base_bytes, len(base_bytes)
    )
    if not lib.ada_is_valid(urlobj):
        raise ValueError('Invalid URL') from None

    return _get_str(lib.ada_get_href(urlobj))


def normalize_url(s):
    """
    Returns a "normalized" URL with all ``'..'`` and ``'/'`` characters resolved.

    .. code-block:: python

        >>> from ada_url import normalize_url
        >>> normalize_url('http://a/b/c/../g')
        'http://a/b/g'

    """
    return parse_url(s, attributes=('href',))['href']


def parse_url(s, attributes=PARSE_ATTRIBUTES):
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
            'origin': 'https://example.org:8080'
        }

    The names of the dictionary keys correspond to the components of the "URL class"
    in the WHATWG URL spec.

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
    urlobj = _get_urlobj(lib.ada_parse, s_bytes, len(s_bytes))
    if not lib.ada_is_valid(urlobj):
        raise ValueError('Invalid URL') from None

    for attr in attributes:
        get_func = getattr(lib, f'ada_get_{attr}')
        data = get_func(urlobj)
        ret[attr] = _get_str(data)
        if attr == 'origin':
            lib.ada_free_owned_string(data)

    return ret


def replace_url(s, **kwargs):
    """
    Start with the URL represented by *s*, replace the attributes given in the *kwargs*
    mapping, and return a normalized URL with the result.

    Raises ``ValueError`` if the input URL or one of the components is not valid.

    .. code-block:: python

        >>> from ada_url import replace_url
        >>> base_url = 'https://user_1:password_1@example.org/resource'
        >>> replace_url(base_url, username='user_2', protocol='http:')
        'http://user_2:password_1@example.org/resource'

    Unrecognized attributes are ignored. ``href`` is replaced first if it is given.
    ``hostname`` is replaced before ``host`` if both are given.

    """
    try:
        s_bytes = s.encode('utf-8')
    except Exception:
        raise ValueError('Invalid URL') from None

    urlobj = _get_urlobj(lib.ada_parse, s_bytes, len(s_bytes))
    if not lib.ada_is_valid(urlobj):
        raise ValueError('Invalid URL') from None

    for attr in URL_ATTRIBUTES:
        value = kwargs.get(attr)
        if value is None:
            continue

        try:
            value_bytes = value.encode()
        except Exception:
            raise ValueError(f'Invalid value for {attr}') from None

        set_func = getattr(lib, f'ada_set_{attr}')
        set_result = set_func(urlobj, value_bytes, len(value_bytes))
        if (set_result is not None) and (not set_result):
            raise ValueError(f'Invalid value for {attr}') from None

    return _get_str(lib.ada_get_href(urlobj))
