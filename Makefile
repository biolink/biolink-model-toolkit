dev-install:
	poetry install

install:
	poetry install

test:
	poetry run pytest tests/*

cleandist:
	rm -rf dist/
	rm -rf build/
