dev-install:
	poetry install

install:
	poetry install

test:
	pytest tests/*

cleandist:
	rm -rf dist/
	rm -rf build/
