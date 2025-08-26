"""Thin alias module resolving to the canonical app implementation.

This file simply re-exports create_app (and app if present) from
invoice_portal.invoice_portal.app to avoid import cycles.
"""

from .invoice_portal.app import create_app  # type: ignore F401

try:
    from .invoice_portal.app import app  # type: ignore F401
except Exception:  # pragma: no cover
    app = None
