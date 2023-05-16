what-url
========

This is ``what_url``, a Python library for parsing and joining URLs.

Examples
--------

.. code-block:: python

    >>> import what_url
    >>> what_url.check_url('https://example.org')
    True
    >>> what_url.join_url(
        'https://example.org/dir/child.txt', '../parent.txt'
    )
    'https://example.org/parent.txt'
    >>> what_url.normalize_url('https://example.org/dir/../parent.txt')
    'https://example.org/parent.txt'
    >>> what_url.parse_url('https://user:pass@example.org:80/api?q=1#2')
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
