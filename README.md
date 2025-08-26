Invoice Portal (Flask + HTMX) — Deployment Guide

Overview

- Client-facing invoice portal built with Flask, Jinja, and HTMX.
- Stateless server: no database or sessions. All invoice data lives in the browser (localStorage) and is posted with each request via HTMX.
- Users can view/filter invoices, see details and totals, update billing info, and download/print an invoice HTML that browsers can “Save as PDF”.

Architecture

- Server: Flask renders templates only; it does not persist data.
- Client data: stored as YAML in `localStorage` under key `invoice_portal_data` and automatically attached to HTMX requests.
- Templates: Jinja templates under `templates/` compose the UI and partials.
- Static: CSS in `static/` served by Flask or a reverse proxy.

Prerequisites

- Python 3.10+ (3.11/3.12 recommended)
- Pip and virtualenv (or uv/pipx/poetry if you prefer)
- Production web server: either Gunicorn (recommended) or a container runtime (Docker/Containerd)
- Optional: Nginx or another reverse proxy/ingress for TLS and compression

Local Development (Quick Start)

1) Create a virtual environment and install dependencies

   ```bash
   cd invoice_portal
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2) Run the development server

   ```bash
   FLASK_APP=invoice_portal.app FLASK_ENV=development flask run --host 0.0.0.0 --port 5000
   # or: python -m flask --app invoice_portal.app run --host 0.0.0.0 --port 5000
   ```

3) Open http://localhost:5000 and use the “Your Data” panel to paste/import YAML (or visit Designer) and click “Save”.

Production Deployment Options

Option A — Gunicorn + systemd (Ubuntu/Debian)

1) Install system packages and Python deps

   ```bash
   sudo apt-get update && sudo apt-get install -y python3-venv
   cd /opt/invoice_portal
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r invoice_portal/requirements.txt
   # Add Gunicorn for production WSGI
   pip install gunicorn
   ```

2) Test Gunicorn locally

   ```bash
   .venv/bin/gunicorn -w 2 -k gthread -b 0.0.0.0:8000 invoice_portal.app:app
   ```

3) Create a systemd unit at `/etc/systemd/system/invoice-portal.service`

   ```ini
   [Unit]
   Description=Invoice Portal (Flask via Gunicorn)
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/opt/invoice_portal
   Environment=PYTHONUNBUFFERED=1
   ExecStart=/opt/invoice_portal/.venv/bin/gunicorn -w 2 -k gthread -b 127.0.0.1:8000 invoice_portal.app:app
   Restart=on-failure
   User=www-data
   Group=www-data

   [Install]
   WantedBy=multi-user.target
   ```

4) Start and enable

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now invoice-portal
   systemctl status invoice-portal
   ```

Option B — Docker Container

Create `Dockerfile` in the repo root:

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY invoice_portal/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && pip install gunicorn
COPY invoice_portal /app/invoice_portal
EXPOSE 8000
CMD ["gunicorn","-w","2","-k","gthread","-b","0.0.0.0:8000","invoice_portal.app:app"]
```

Build and run:

```bash
docker build -t invoice-portal:latest .
docker run --rm -p 8000:8000 invoice-portal:latest
```

Option C — Kubernetes (example manifests)

Minimal Deployment/Service (adjust image reference):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: invoice-portal
spec:
  replicas: 2
  selector:
    matchLabels:
      app: invoice-portal
  template:
    metadata:
      labels:
        app: invoice-portal
    spec:
      containers:
        - name: web
          image: your-registry/invoice-portal:latest
          ports:
            - containerPort: 8000
          readinessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: invoice-portal
spec:
  selector:
    app: invoice-portal
  ports:
    - port: 80
      targetPort: 8000
```

Ingress (Nginx Ingress Controller example):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: invoice-portal
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "1m"
spec:
  rules:
    - host: invoices.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: invoice-portal
                port:
                  number: 80
  tls:
    - hosts: ["invoices.example.com"]
      secretName: invoices-tls
```

Reverse Proxy (Nginx)

Terminate TLS at Nginx and proxy to Gunicorn on localhost:

```nginx
server {
  listen 443 ssl http2;
  server_name invoices.example.com;
  ssl_certificate     /etc/letsencrypt/live/invoices.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/invoices.example.com/privkey.pem;

  location /static/ {
    alias /opt/invoice_portal/invoice_portal/static/;
    expires 7d;
    add_header Cache-Control "public";
  }

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}

server {
  listen 80;
  server_name invoices.example.com;
  return 301 https://$host$request_uri;
}
```

Configuration

- App import path: `invoice_portal.app:app` (WSGI).
- Bind address: controlled by your process manager (Gunicorn `-b`, Docker `-p`).
- Environment variables used by Flask CLI only:
  - `FLASK_APP=invoice_portal.app`
  - `FLASK_ENV=production` in prod (or omit for default production settings in Flask 3).
- Path base: the app expects to run at site root `/`. If you must serve under a subpath, ensure the reverse proxy rewrites to `/` or mount the app with a proper `SCRIPT_NAME`—routes and links are absolute.

Health Checks

- Liveness/readiness: `GET /` returns HTTP 200 and serves the shell UI. Use this for probes.
- No database or external dependencies; a 200 from `/` indicates the app is healthy.

Security Notes

- TLS: always serve behind HTTPS when exposed publicly.
- Cookies/sessions: not used. HTMX is configured with `withCredentials: true` but the app does not set cookies.
- Data privacy: invoice data lives in the end-user’s browser. Nothing is stored server-side unless you add integrations.
- Content limits: requests are small YAML payloads posted by the browser; default Flask limits are sufficient. If you later add uploads, adjust proxy/body size.

Upgrades and Zero-Downtime

- Gunicorn: use multiple workers (`-w 2+`) and a reverse proxy to drain connections during reloads (`systemctl restart` performs a quick restart).
- Containers/Kubernetes: roll out with a rolling update; readiness probes ensure traffic only hits healthy pods.

Troubleshooting

- Blank invoice list: ensure you saved data via “Your Data” or Designer. The server has no database.
- 404 on invoice detail: the posted YAML must include the invoice ID you are trying to open.
- Static assets missing: confirm Nginx `alias` path matches your install path, or let Flask serve `/static/` directly without Nginx alias during initial setup.

Project Structure

```
invoice_portal/
├── app.py            # Flask app and routes
├── requirements.txt  # Flask runtime deps
├── seed.py           # Sample data generator (prints YAML)
├── static/
│   └── styles.css
└── templates/
    ├── _invoice_rows.html
    ├── base.html
    ├── billing_info.html
    ├── client_shell.html
    ├── designer.html
    ├── invoice_detail.html
    └── invoice_pdf.html
```

Notes

- PDF export: `/invoice/<id>/pdf` returns print-friendly HTML. Users can print or save as PDF in their browser. To add server-side PDF rendering later, consider WeasyPrint or wkhtmltopdf in the Gunicorn command.
- Sample data: run `python invoice_portal/seed.py` to print demo YAML you can paste into the UI.
