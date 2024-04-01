ada-url
========

The `urlib.parse` module in Python does not follow the legacy RFC 3978 standard nor
does it follow the newer WHATWG URL specification. It is also relatively slow.

This is ``ada_url``, a fast standard-compliant Python library for working with URLs based on the ``Ada`` URL
parser.

* `Documentation <https://ada-url.readthedocs.io>`__
* `Development <https://github.com/ada-url/ada-python/>`__
* `Ada <https://www.ada-url.com/>`__ 

Installation
------------

Install from `PyPI <https://pypi.org/project/ada-url/>`__:

.. code-block:: sh

    pip install ada_url

Usage examples
--------------

Parsing URLs
^^^^^^^^^^^^

The ``URL`` class is intended to match the one described in the
`WHATWG URL spec <https://url.spec.whatwg.org/#url-class>`_:.

.. code-block:: python

    >>> from ada_url import URL
    >>> urlobj = URL('https://example.org/path/../file.txt')
    >>> urlobj.href
    'https://example.org/path/file.txt'

The ``parse_url`` function returns a dictionary of all URL elements:

.. code-block:: python

    >>> from ada_url import parse_url
    >>> parse_url('https://user:pass@example.org:80/api?q=1#2')
    {
        'href': 'https://user:pass@example.org:80/api?q=1#2',
        'username': 'user',
        'password': 'pass',
        'protocol': 'https:',
        'port': '80',
        'hostname': 'example.org',
        'host': 'example.org:80',
        'pathname': '/api',
        'search': '?q=1',
        'hash': '#2',
        'origin': 'https://example.org:80',
        'host_type': <HostType.DEFAULT: 0>,
        'scheme_type': <SchemeType.HTTPS: 2>
    }

Altering URLs
^^^^^^^^^^^^^

Replacing URL components with the ``URL`` class:

.. code-block:: python

    >>> from ada_url import URL
    >>> urlobj = URL('https://example.org/path/../file.txt')
    >>> urlobj.host = 'example.com'
    >>> urlobj.href
    'https://example.com/file.txt'

Replacing URL components with the ``replace_url`` function:

    >>> from ada_url import replace_url
    >>> replace_url('https://example.org/path/../file.txt', host='example.com')
    'https://example.com/file.txt'

Search parameters
^^^^^^^^^^^^^^^^^

The ``URLSearchParams`` class is intended to match the one described in the
`WHATWG URL spec <https://url.spec.whatwg.org/#interface-urlsearchparams>`__.

.. code-block:: python

    >>> from ada_url import URLSearchParams
    >>> obj = URLSearchParams('key1=value1&key2=value2')
    >>> list(obj.items())
    [('key1', 'value1'), ('key2', 'value2')]

The ``parse_search_params`` function returns a dictionary of search keys mapped to
value lists:

.. code-block:: python

    >>> from ada_url import parse_search_params
    >>> parse_search_params('key1=value1&key2=value2')
    {'key1': ['value1'], 'key2': ['value2']}

Internationalized domain names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``idna`` class can encode and decode IDNs:

.. code-block:: python

    >>> from ada_url import idna
    >>> idna.encode('Bücher.example')
    b'xn--bcher-kva.example'
    >>> idna.decode(b'xn--bcher-kva.example')
    'bücher.example'

WHATWG URL compliance
---------------------

This library is compliant with the WHATWG URL spec. This means, among other things,
that it properly encodes IDNs and resolves paths:

.. code-block:: python

    >>> from ada_url import URL
    >>> parsed_url = URL('https://www.GOoglé.com/./path/../path2/')
    >>> parsed_url.hostname
    'www.xn--googl-fsa.com'
    >>> parsed_url.pathname
    '/path2/'

Contrast that with the Python standard library's ``urlib.parse`` module:

.. code-block:: python

    >>> from urllib.parse import urlparse
    >>> parsed_url = urlparse('https://www.GOoglé.com/./path/../path2/')
    >>> parsed_url.hostname
    'www.googlé.com'
    >>> parsed_url.path
    '/./path/../path2/'

Alternative Python bindings
---------------------------

This package uses `CFFI <https://github.com/ada-url/ada-python/>`__ to call
the ``Ada`` library's functions, which has a performance cost.
The alternative `can_ada <https://github.com/ada-url/ada-python/>`__ (Canadian Ada)
package uses `pybind11 <https://pybind11.readthedocs.io/en/stable/>`__ to generate a
Python extension module, which is more performant.
