.PHONY: requirements
requirements:
	python3 -m pip install -r requirements/development.txt

.PHONY: check
check:
	black --check .
	ruff .

.PHONY: format
format:
	black .

.PHONY: coverage
coverage:
	coverage run -m unittest
	coverage report --show-missing --fail-under 99

.PHONY: test
test:
	python -m unittest -v ${tests}

.PHONY: docs
docs:
	sphinx-build -W -b html docs docs/_build/html

.PHONY: clean
clean:
	rm -rf _build/
	rm -rf _dist/
	rm -rf ada_url.egg-info/
	rm -f ada_url/_ada_wrapper.abi3.so
	rm -f ada_url/ada.o

.PHONY: package
package:
	c++ -c "ada_url/ada.cpp" -fPIC -std="c++17" -O2 -o "ada_url/ada.o"
	python -m build --no-isolation
	twine check dist/*
