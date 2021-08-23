dev-install:
	pip install -e .

install:
	python setup.py install

test:
	pytest tests/*

cleandist:
	rm -rf dist/
	rm -rf build/
