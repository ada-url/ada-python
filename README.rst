ada-url
========


This is ``ada_url``, a Python library for parsing and joining URLs.


WHATWG URL compliance
---------------------

Unlike the standard library's ``urllib.parse`` module, this library is compliant with the WHATWG URL spec.

.. code-block:: python

    urlstring = "https://www.GOoglé.com/./path/../path2/"

    import ada_url

    # prints www.xn--googl-fsa.com,
    # the correctly parsed domain name according to WHATWG
    print(ada_url.URL(urlstring).hostname)
    # prints /path2/
    # the correctly parsed pathname according to WHATWG
    print(ada_url.URL(urlstring).pathname)

    import urllib

    #prints www.googlé.com
    print(urllib.parse.urlparse(urlstring).hostname)
    #prints /./path/../path2/
    print(urllib.parse.urlparse(urlstring).path)


Examples
--------

This package exposes a ``URL`` class that is intended to match the one described in the
`WHATWG URL spec <https://url.spec.whatwg.org/#url-class>`__.

.. code-block:: python

    >>> import ada_url
    >>> ada_url.URL('https://example.org/path/../file.txt') as urlobj:
    >>> urlobj.host = 'example.com'
    >>> new_url = urlobj.href
    >>> new_url
    'https://example.com/file.txt'

It also provides some higher level functions for parsing and manipulating URLs.

.. code-block:: python

    >>> import ada_url
    >>> ada_url.check_url('https://example.org')
    True
    >>> ada_url.join_url(
        'https://example.org/dir/child.txt', '../parent.txt'
    )
    'https://example.org/parent.txt'
    >>> ada_url.normalize_url('https://example.org/dir/../parent.txt')
    'https://example.org/parent.txt'
    >>> ada_url.parse_url('https://user:pass@example.org:80/api?q=1#2')
    {
        'href': 'https://user:pass@example.org:80/api?q=1#2',
        'username': 'user',
        'password': 'pass',
        'protocol': 'https:',
        'host': 'example.org:80',
        'port': '80',
        'hostname': 'example.org',
        'pathname': '/api',
        'search': '?q=1',
        'hash': '#2'
    }
    >>> ada_url.replace_url('http://example.org:80', protocol='https:')
    'https://example.org/'
