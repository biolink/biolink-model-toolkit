dev-install:
	pip install -e .

install:
	python setup.py install

release:
	pip install twine
	rm -rf dist/
	rm -rf build/
	python setup.py sdist bdist_wheel
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
