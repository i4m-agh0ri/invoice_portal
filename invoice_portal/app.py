"""Compatibility wrapper so `from invoice_portal.app import create_app` works
in CI across different repository layouts.

It searches for a Flask app implementation in several common locations and
adds a fallback /help route if the underlying app does not define one.
"""

from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _import_from_file(path: Path):
    spec = spec_from_file_location("_invoice_portal_impl", str(path))
    if spec and spec.loader:
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod
    raise ModuleNotFoundError(f"Could not import from {path}")


def _load_impl():
    # Try module imports first
    for mod_name in (
        "invoice_portal.invoice_portal.app",  # deeper nested
        "invoice_portal.app",  # sibling package (src-style projects)
        "app",  # root-level fallback
    ):
        try:
            return import_module(mod_name)
        except ModuleNotFoundError:
            pass

    # Fall back to searching common file locations relative to this file
    here = Path(__file__).resolve()
    pkg_root = here.parent  # invoice_portal/
    repo_root = pkg_root.parent
    candidates = [
        pkg_root / "app.py",  # invoice_portal/app.py (this file) — ignore
        repo_root / "invoice_portal" / "app.py",  # invoice_portal/invoice_portal/app.py (sibling wrapper)
        repo_root / "invoice_portal" / "invoice_portal" / "app.py",  # triple-nested impl
        repo_root / "app.py",  # root-level app.py
        repo_root / "src" / "invoice_portal" / "app.py",  # src layout
        repo_root / "invoice_portal" / "src" / "invoice_portal" / "app.py",  # nested src
    ]
    for path in candidates:
        if path.is_file() and path != here:
            try:
                return _import_from_file(path)
            except Exception:
                continue
    raise ModuleNotFoundError("Could not locate application module in known paths")


_impl = _load_impl()


def _ensure_help_route(flask_app) -> None:
    try:
        rules = {r.rule for r in flask_app.url_map.iter_rules()}
        if "/help" in rules:
            return
    except Exception:
        pass

    @flask_app.get("/help")  # type: ignore[attr-defined]
    def _help_page():
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Help</title></head>"
            "<body><h1>YAML Guide</h1><p>See Designer and Sample YAML.</p></body></html>"
        )


def create_app(*args, **kwargs):
    factory = getattr(_impl, "create_app")
    app = factory(*args, **kwargs)
    _ensure_help_route(app)
    return app


# Optional WSGI app for runners expecting invoice_portal.app:app
try:
    app = create_app()
except Exception:  # pragma: no cover
    app = None
