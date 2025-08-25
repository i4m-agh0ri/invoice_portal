.PHONY: venv install dev serve test perf perf-invoices perf-pdf help

VENV := .venv
PY ?= python
K6 ?= k6

help:
	@echo "Targets:"
	@echo "  make venv          # Create venv and install runtime deps"
	@echo "  make install       # venv + gunicorn (for perf/server)"
	@echo "  make dev           # Run Flask dev server on :5000"
	@echo "  make serve         # Run gunicorn on 127.0.0.1:8000"
	@echo "  make test          # Run unit tests"
	@echo "  make perf          # Run both k6 perf scripts"
	@echo "  make perf-invoices # k6 load test for /invoices"
	@echo "  make perf-pdf      # k6 load test for /invoice/1/pdf"

venv:
	$(PY) -m venv $(VENV)
	. $(VENV)/bin/activate; pip install -r invoice_portal/requirements.txt

install: venv
	. $(VENV)/bin/activate; pip install gunicorn

dev: venv
	. $(VENV)/bin/activate; FLASK_APP=invoice_portal.app FLASK_ENV=development flask run -p 5000

serve: install
	. $(VENV)/bin/activate; gunicorn -w 2 -k gthread -b 127.0.0.1:8000 invoice_portal.app:app

test: venv
	. $(VENV)/bin/activate; python -m unittest discover -s tests -p "test_*.py" -v

perf-invoices:
	$(K6) run tests/perf/k6-invoices.js

perf-pdf:
	$(K6) run tests/perf/k6-pdf.js

perf: perf-invoices perf-pdf
