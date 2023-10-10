.. include:: ./_build/README.pprst

Building from source
====================

You will need to have Python 3 development files installed.
On macOS, you will have these if you installed Python with ``brew``.
On Linux, you may need to install some packages (e.g., ``python3-dev`` and ``python3-venv``).

You will also need a C++ toolchain.
On macOS, Xcode will provide this for you.
On Linux, you may need to install some more pacakges (e.g. ``build-esential``).

Clone the git repository to a directory for development:

.. code-block:: sh

    git clone https://github.com/ada-url/ada-python.git ada_url_python
    cd ada_url_python

Create a virtual environment to use for building:

.. code-block:: sh

    python3 -m venv env
    source ./env/bin/activate

After that, you're ready to build the package:

.. code-block:: sh

    python -m pip install -r requirements/development.txt
    c++ -c "ada_url/ada.cpp" -fPIC -std="c++17" -O2 -o "ada_url/ada.o"
    python -m build --no-isolation

This will create a `.whl` file in the `dist` directory. You can install it in other
virtual environments on the same machine.

To run tests, first build a package. Then:

 .. code-block:: sh

    python -m pip install -e .
    python -m unittest

Leave the virtual environment with the ``deactivate`` comamnd.

API Documentation
=================

.. automodule:: ada_url

.. autoclass:: URL(url, base=None)
.. autoclass:: HostType()
.. autoclass:: SchemeType()
.. autofunction:: check_url(s)
.. autofunction:: join_url(base_url, s)
.. autofunction:: normalize_url(s)
.. autofunction:: parse_url(s, [attributes])
.. autofunction:: replace_url(s, **kwargs)
.. autoclass:: URLSearchParams(params)
.. autoclass:: parse_search_params(s)
.. autoclass:: replace_search_params(s)
.. autoclass:: idna

