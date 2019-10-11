export PYTHONDONTWRITEBYTECODE=1

test:
	ASYNC_TEST_TIMEOUT=30.0 pytest -x --no-cov

coverage:
	ASYNC_TEST_TIMEOUT=30.0 pytest -x --no-cov-on-fail --cov --cov-report=term

clean:
	rm -rf cover/

requirements-dev:
	@pip install -r requirements/development.txt

outdated: ## Show outdated dependencies
	@pip list --outdated --format=columns
