OS := $(shell uname)

test:
	poetry run pytest -vv

lint:
	poetry run ruff check $(if $(GITHUB_ACTIONS),--output-format github,) .

format:
	poetry run ruff format

coverage:
	poetry run pytest -q --cov=bookworm_genai --cov-report=term # for local
	poetry run pytest -q --cov=bookworm_genai --cov-report=html # for local

	# for sonarqube
	$(if $(GITHUB_ACTIONS),poetry run pytest -q --cov=bookworm_genai --cov-report=xml,)

	# for github action
	$(if $(GITHUB_ACTIONS),poetry run pytest -q --cov=bookworm_genai --cov-report=lcov,)

check_database:
ifeq ($(OS),Darwin)
	duckdb "/Users/kiran/Library/Application Support/bookworm/bookmarks.duckdb" -c 'SELECT * FROM embeddings LIMIT 5; SELECT COUNT(*) FROM embeddings'
else ifeq ($(OS),Linux)
	duckdb ~/.local/share/bookworm/bookmarks.duckdb -c 'SELECT * FROM embeddings LIMIT 5; SELECT COUNT(*) FROM embeddings'
else
	@echo "OS not supported"
endif

# Useful if you are running on non-linux machine
# and want to verify tests are still working on that platform
docker_linux:
	docker build -f Dockerfile.linux -t bookworm_linux .
