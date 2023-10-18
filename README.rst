ada-url
========


This is ``ada_url``, a Python library for parsing and joining URLs.

Installation
------------

Install from `PyPI <https://pypi.org/project/ada-url/>`__:

.. code-block:: sh

    pip install ada_url

Usage examples
--------------

This package exposes a ``URL`` class that is intended to match the one described in the
`WHATWG URL spec <https://url.spec.whatwg.org/#url-class>`__.

.. code-block:: python

    >>> from ada_url import URL
    >>> URL('https://example.org/path/../file.txt') as urlobj:
    >>> urlobj.host = 'example.com'
    >>> new_url = urlobj.href
    >>> new_url
    'https://example.com/file.txt'

It also provides high level functions for parsing and manipulating URLs. Validating
a URL:

.. code-block:: python

    >>> from ada_url import check_url
    >>> check_url('https://example.org')
    True
    >>> check_url('http://example:bougus')
    False

Parsing a URL:

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

Replacing URL components:

.. code-block:: python

    >>> from ada_url import replace_url
    >>> ada_url.replace_url('http://example.org:80', protocol='https:')
    'https://example.org/'

Joining a URL with a relative fragment:

    >>> from ada_url import join_url
    >>> join_url('https://example.org/dir/child.txt', '../parent.txt')
    'https://example.org/parent.txt'

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
    >>> parsed_url = urlparse()
    >>> parsed_url.hostname
    'www.googlé.com'
    >>> parsed_url.path
    '/./path/../path2/'

More information
----------------

* ``ada-url`` is based on the `Ada <https://www.ada-url.com/>`__ project.
* A full API reference is available at `Read the Docs <https://ada-url.readthedocs.io>`__.
* Source code is available at `GitHub <https://github.com/ada-url/ada-python>`__.
