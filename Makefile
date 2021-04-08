dev-install:
	pip install -e .

install:
	python setup.py install

tests:
	pytest tests/*

cleandist:
	rm -rf dist/
	rm -rf build/
