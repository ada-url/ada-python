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


def _get_str(x):
    ret = ffi.string(x.data, x.length).decode('utf-8') if x.length else ''
    return ret


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

    urlobj = lib.ada_parse(s_bytes, len(s_bytes))
    try:
        return lib.ada_is_valid(urlobj)
    finally:
        lib.ada_free(urlobj)


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

    urlobj = lib.ada_parse_with_base(s_bytes, len(s_bytes), base_bytes, len(base_bytes))
    try:
        if not lib.ada_is_valid(urlobj):
            raise ValueError('Invalid URL') from None

        return _get_str(lib.ada_get_href(urlobj))
    finally:
        lib.ada_free(urlobj)


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
    urlobj = lib.ada_parse(s_bytes, len(s_bytes))
    try:
        if not lib.ada_is_valid(urlobj):
            raise ValueError('Invalid URL') from None

        for attr in attributes:
            get_func = getattr(lib, f'ada_get_{attr}')
            data = get_func(urlobj)
            ret[attr] = _get_str(data)
            if attr == 'origin':
                lib.ada_free_owned_string(data)
    finally:
        lib.ada_free(urlobj)

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

    urlobj = lib.ada_parse(s_bytes, len(s_bytes))
    try:
        if not lib.ada_is_valid(urlobj):
            raise ValueError('Invalid URL') from None

        for attr in URL_ATTRIBUTES:
            value = kwargs.get(attr)
            if not value:
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
    finally:
        lib.ada_free(urlobj)
