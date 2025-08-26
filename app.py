from __future__ import annotations

from flask import Flask, abort, make_response, render_template, request
import yaml


def _parse_client_data() -> dict:
    # Accept YAML only
    raw = request.form.get("client_data")
    if raw is None:
        raw = request.get_data(as_text=True) or ""
    if not isinstance(raw, str):
        return {}
    raw = raw.strip()
    if not raw:
        return {}
    try:
        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _totals_for_invoice(inv: dict, items: list[dict], payments: list[dict]) -> dict:
    subtotal = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)
    tax_rate = inv.get("tax_rate", 0.0)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    paid = round(sum(p.get("amount", 0) for p in payments), 2)
    due = round(total - paid, 2)
    return {"subtotal": subtotal, "tax": tax, "total": total, "paid": paid, "due": due}


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    @app.get("/")
    def shell():
        return render_template("client_shell.html")

    @app.get("/help")
    def help_page():
        return render_template("help.html")

    @app.get("/designer")
    def designer():
        return render_template("designer.html")

    @app.post("/invoices")
    def invoices():
        data = _parse_client_data()
        status = request.form.get("status", "all")

        client = data.get("client", {})
        invoices = data.get("invoices", [])
        items = data.get("items", [])
        payments = data.get("payments", [])

        # Compose per-invoice data
        inv_list = []
        totals_map = {}
        for inv in invoices:
            inv_id = inv.get("id")
            inv_items = [it for it in items if it.get("invoice_id") == inv_id]
            inv_payments = [p for p in payments if p.get("invoice_id") == inv_id]
            totals = _totals_for_invoice(inv, inv_items, inv_payments)
            # Compute derived status for overdue if needed
            derived_status = inv.get("status", "open")
            if derived_status == "open" and inv.get("due_date") and totals["due"] > 0:
                # naive overdue check can be enhanced client-side as needed
                derived_status = inv.get("status")
            inv_copy = {**inv, "derived_status": derived_status}
            totals_map[str(inv_id)] = totals
            inv_list.append(inv_copy)

        if status in ("open", "paid", "overdue"):
            inv_list = [i for i in inv_list if i.get("status") == status or i.get("derived_status") == status]

        return render_template("invoices.html", client=client, invoices=inv_list, totals_map=totals_map, active=status)

    @app.post("/invoice/<int:invoice_id>")
    def invoice_detail(invoice_id: int):
        data = _parse_client_data()
        client = data.get("client", {})
        invoices = data.get("invoices", [])
        items = data.get("items", [])
        payments = data.get("payments", [])
        inv = next((i for i in invoices if i.get("id") == invoice_id), None)
        if not inv:
            abort(404)
        inv_items = [it for it in items if it.get("invoice_id") == invoice_id]
        inv_payments = [p for p in payments if p.get("invoice_id") == invoice_id]
        totals = _totals_for_invoice(inv, inv_items, inv_payments)
        return render_template("invoice_detail.html", client=client, invoice=inv, items=inv_items, totals=totals)

    @app.post("/invoice/<int:invoice_id>/billing")
    def billing_info(invoice_id: int):
        data = _parse_client_data()
        client = data.get("client", {})
        return render_template("billing_info.html", client=client)

    @app.post("/invoice/<int:invoice_id>/pdf")
    def invoice_pdf(invoice_id: int):
        data = _parse_client_data()
        client = data.get("client", {})
        invoices = data.get("invoices", [])
        items = data.get("items", [])
        payments = data.get("payments", [])
        auto_print = request.form.get("auto_print") == "1"
        inv = next((i for i in invoices if i.get("id") == invoice_id), None)
        if not inv:
            abort(404)
        inv_items = [it for it in items if it.get("invoice_id") == invoice_id]
        inv_payments = [p for p in payments if p.get("invoice_id") == invoice_id]
        totals = _totals_for_invoice(inv, inv_items, inv_payments)
        html = render_template("invoice_pdf.html", client=client, invoice=inv, items=inv_items, totals=totals, auto_print=auto_print)
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Content-Disposition"] = f"inline; filename=invoice-{inv.get('number','invoice')}.html"
        return resp

    return app


app = create_app()
