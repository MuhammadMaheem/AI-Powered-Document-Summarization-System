.PHONY: install setup run test clean

install:
	pip install -r requirements.txt

setup: install
	python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
	python -m spacy download en_core_web_sm

run:
	python run.py

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	rm -rf .pytest_cache; \
	echo "Cleaned."
