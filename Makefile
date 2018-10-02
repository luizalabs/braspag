export PYTHONDONTWRITEBYTECODE=1

test:
	ASYNC_TEST_TIMEOUT=30.0 nosetests -v --stop --with-coverage --cover-package=braspag

coverage:
	ASYNC_TEST_TIMEOUT=30.0 nosetests -v --stop --with-coverage --cover-package=braspag --cover-html
	open cover/index.html

clean:
	rm -rf cover/

requirements-dev:
	@pip install -r requirements/development.txt

outdated: ## Show outdated dependencies
	@pip list --outdated --format=columns
