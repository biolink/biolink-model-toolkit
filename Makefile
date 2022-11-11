dev-install:
	poetry install

install:
	poetry install

test:
	poery run pytest tests/*

cleandist:
	rm -rf dist/
	rm -rf build/
