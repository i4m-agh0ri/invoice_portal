import unittest
from pathlib import Path

from invoice_portal.app import create_app


SAMPLE_PATH = Path(__file__).resolve().parents[1] / "invoice_portal" / "static" / "samples" / "invoices.yaml"


class InvoicePortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_yaml = SAMPLE_PATH.read_text(encoding="utf-8")

    def setUp(self):
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_root_ok(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Your Data", r.data)

    def test_help_ok(self):
        r = self.client.get("/help")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"YAML Guide", r.data)

    def test_designer_ok(self):
        r = self.client.get("/designer")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Data Designer", r.data)

    def test_invoices_empty(self):
        r = self.client.post("/invoices")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"No invoices.", r.data)

    def test_invoices_with_sample(self):
        r = self.client.post("/invoices", data={"client_data": self.sample_yaml})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"INV-1001", r.data)
        self.assertIn(b"INV-1000", r.data)

    def test_invoice_detail_ok(self):
        r = self.client.post("/invoice/1", data={"client_data": self.sample_yaml})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Invoice INV-1001", r.data)
        self.assertIn(b"Bill To", r.data)

    def test_invoice_pdf_headers(self):
        r = self.client.post("/invoice/1/pdf", data={"client_data": self.sample_yaml})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.headers.get("Content-Type", "").startswith("text/html"))
        disp = r.headers.get("Content-Disposition", "")
        self.assertIn("invoice-INV-1001", disp)

    def test_invoice_not_found(self):
        r = self.client.post("/invoice/999", data={"client_data": self.sample_yaml})
        self.assertEqual(r.status_code, 404)

    def test_static_sample_served(self):
        r = self.client.get("/static/samples/invoices.yaml")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data.startswith(b"client:"))

    def test_yaml_malicious_is_ignored(self):
        # safe_load should reject python-specific tags; app should not crash and shows no invoices
        malicious = "!!python/object/apply:os.system ['echo hi']\n"
        r = self.client.post("/invoices", data={"client_data": malicious})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"No invoices.", r.data)

    def test_totals_math_from_sample(self):
        # For invoice 1 in sample: subtotal=3200.00, tax=224.00 (7%), total=3424.00
        r = self.client.post("/invoice/1", data={"client_data": self.sample_yaml})
        self.assertEqual(r.status_code, 200)
        body = r.data.decode("utf-8")
        self.assertIn("USD 3,200.00".replace(",", ""), body)  # ensure two-decimal currency appears
        self.assertIn("USD 224.00", body)
        self.assertIn("USD 3424.00", body)


if __name__ == "__main__":
    unittest.main()

