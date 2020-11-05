dev-install:
	pip install -e .

install:
	python setup.py install

tests:
	pytest test/*

cleandist:
	rm -rf dist/
	rm -rf build/
