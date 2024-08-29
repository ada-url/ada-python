.PHONY: requirements
requirements:
	python -m pip install -U -r requirements/development.txt ${req_args}

.PHONY: check
check:
	ruff check .

.PHONY: format
format:
	ruff format .

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
	$(RM) ada_url/_ada_wrapper.abi3.so
	$(RM) ada_url/ada.o

.PHONY: package
package:
	python -m build --no-isolation
	twine check dist/*
