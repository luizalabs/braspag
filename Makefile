export PYTHONDONTWRITEBYTECODE=1

test:
	@pytest -x --no-cov

coverage:
	@pytest -x --no-cov-on-fail --cov --cov-report=term

clean:
	rm -rf cover/

requirements-dev:
	@pip install -r requirements/development.txt

outdated: ## Show outdated dependencies
	@pip list --outdated --format=columns
