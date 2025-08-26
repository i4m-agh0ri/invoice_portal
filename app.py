"""Compatibility wrapper so tests can import invoice_portal.app
across different layouts (nested package or root app module)."""

from importlib import import_module


def _load_impl():
    # Prefer canonical nested package if present
    for mod_name in (
        'invoice_portal.invoice_portal.app',  # nested package
        'app',  # root-level app.py fallback
    ):
        try:
            return import_module(mod_name)
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError("Could not locate application module 'invoice_portal.invoice_portal.app' or 'app'")


_impl = _load_impl()
create_app = getattr(_impl, 'create_app')

# Optional: expose a default app for WSGI runners expecting invoice_portal.app:app
try:
    app = create_app()
except Exception:  # pragma: no cover - avoid hard failure on import if env not ready
    app = None

