.PHONY: default clean dist

default:
	@echo "please select a target"; exit 1

clean:
	rm -rf dist/

dist:
	python -m build
	source .env 2>/dev/null || :; twine upload 'dist/*'
