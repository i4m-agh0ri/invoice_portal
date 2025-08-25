from __future__ import annotations

import yaml
from datetime import date, timedelta


def demo_data() -> dict:
    today = date.today()
    data = {
        "client": {
            "name": "Acme Corp",
            "email": "acme@example.com",
            "address_line1": "123 Market St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "US",
            "tax_id": "US-123456789",
        },
        "invoices": [
            {
                "id": 1,
                "number": "INV-1001",
                "currency": "USD",
                "issue_date": str(today - timedelta(days=5)),
                "due_date": str(today + timedelta(days=25)),
                "status": "open",
                "tax_rate": 0.07,
                "notes": "Thank you for your business!",
            },
            {
                "id": 2,
                "number": "INV-1000",
                "currency": "USD",
                "issue_date": str(today - timedelta(days=40)),
                "due_date": str(today - timedelta(days=10)),
                "status": "paid",
                "tax_rate": 0.07,
                "notes": "Paid in full",
            },
        ],
        "items": [
            {"invoice_id": 1, "description": "Design work", "quantity": 10, "unit_price": 80},
            {"invoice_id": 1, "description": "Development", "quantity": 20, "unit_price": 120},
            {"invoice_id": 2, "description": "Initial retainer", "quantity": 1, "unit_price": 5000},
        ],
        "payments": [
            {"invoice_id": 2, "amount": 5350, "currency": "USD", "method": "seed", "reference": "paid"}
        ],
    }
    return data


if __name__ == "__main__":
    print(yaml.safe_dump(demo_data(), sort_keys=False))
