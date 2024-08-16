test:
	poetry run pytest -vv

lint:
	poetry run ruff check $(if $(GITHUB_ACTIONS),--output-format github,) .

coverage:
	poetry run pytest -q --cov=bookworm_genai --cov-report=term # for local
	poetry run pytest -q --cov=bookworm_genai --cov-report=html # for local

	# for sonarqube
	$(if $(GITHUB_ACTIONS),poetry run pytest -q --cov=bookworm_genai --cov-report=xml,)

	# for github action
	$(if $(GITHUB_ACTIONS),poetry run pytest -q --cov=bookworm_genai --cov-report=lcov,)

check_database:
	duckdb ~/.local/share/bookworm/bookmarks.duckdb -c 'SELECT * FROM embeddings LIMIT 5; SELECT COUNT(*) FROM embeddings'

