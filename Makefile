.PHONY: data eda clean-data lint type test eval all

PY := python

data:  ## Download raw dataset into data/raw/ (gitignored)
	$(PY) scripts/download_data.py

eda:  ## Run Phase-1 EDA findings
	$(PY) scripts/eda.py

clean-data:  ## Build cleaned + aggregated parquet in data/processed/
	$(PY) scripts/build_dataset.py

lint:
	ruff check src tests scripts

type:
	mypy

test:
	pytest -q

eval:  ## Train baseline + model and print results table
	$(PY) scripts/run_eval.py

all: lint type test
