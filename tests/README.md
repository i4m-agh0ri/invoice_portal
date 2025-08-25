Test Suite

Run unit tests (no external deps):

- Dev server not required. Uses Flask test client.
- Command: `python -m unittest discover -s tests -p "test_*.py" -v`

Optional: run with pytest (if installed):

- Command: `pytest -q`

Performance tests (k6):

1) Start app with Gunicorn:
   - `gunicorn -w 2 -k gthread -b 127.0.0.1:8000 invoice_portal.app:app`
2) In another shell, run k6:
   - `/path/to/k6 run tests/perf/k6-invoices.js`
   - `/path/to/k6 run tests/perf/k6-pdf.js`

Notes:

- The unit tests load the shared sample YAML from `invoice_portal/static/samples/invoices.yaml`.
- k6 `open()` reads the sample YAML relative to the script path at bundle time.

