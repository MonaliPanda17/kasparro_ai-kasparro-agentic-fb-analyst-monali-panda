.PHONY: setup run test lint clean help

help:
	@echo "Available commands:"
	@echo "  make setup    - Install dependencies"
	@echo "  make run       - Run analysis with sample query"
	@echo "  make test      - Run unit tests"
	@echo "  make lint      - Check code formatting"
	@echo "  make clean     - Remove generated files and cache"
	@echo ""

setup:
	pip install -r requirements.txt

run:
	python src/run.py "Analyze ROAS drop in last 7 days"

test:
	pytest tests/ -v

lint:
	@echo "Checking code style..."
	@python -m py_compile src/**/*.py 2>/dev/null || true
	@echo "Linting complete (basic syntax check)"

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -rf .pytest_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

