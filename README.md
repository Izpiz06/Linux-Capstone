# Research Dataset Catalog

A containerized web application designed to maintain searchable metadata about datasets used in student research. Built with Python (Flask, SQLite, Gunicorn) and engineered specifically for deployment using **Podman** and **Red Hat OpenShift**.

---

## 🎯 Requirements & Features

| Requirement | Implementation Status | Description |
| :--- | :--- | :--- |
| **Add Dataset Metadata** |  Completed | Add name, description, category, format, and external source link. |
| **List & Search** |  Completed | Real-time full-text search across dataset names and descriptions. |
| **Record Size & License** |  Completed | Track storage size (MB, GB, TB) and licensing details (CC BY, MIT, Apache, etc.). |
| **Edit & Remove** |  Completed | Edit metadata fields or safely delete datasets with confirmation. |
| **Assigned Variation** |  Completed | Multi-attribute filtering by **Format**, **Category**, and **License**. |
| **Container & Persistence** |  Completed | Persistent metadata via SQLite on a mounted volume (`/data`). Datasets are referenced by URL and not copied into the image. |
| **Podman & OpenShift Ready** |  Completed | OpenShift SCC-compliant (arbitrary UID, non-root, group 0 permissions), health checks (`/healthz`), PVC, Deployment, Service, and Route manifests. |

---

## 🏗️ Architecture & Storage Strategy

- **Metadata Storage**: Stored in a lightweight SQLite database located at `$DATA_DIR/catalog.db` (defaults to `/data/catalog.db`).
- **Zero-Blob Image**: In accordance with project requirements, actual large dataset files are **not copied** into the container image. Instead, catalog entries track their origin and access via `source` URLs.
- **OpenShift Security**: Containers run under the `restricted-v2` Security Context Constraint (SCC) using arbitrary user IDs with `root` (GID 0) group permissions on `/data` and `/app`.
- **Health Probes**: Built-in `/healthz` endpoint verifying database availability for Kubernetes/OpenShift liveness and readiness probes.

---

## 🚀 Quick Start with Podman

### 1. Build the Container Image
```bash
podman build -t research-dataset-catalog:latest .
```

### 2. Create a Persistent Named Volume
Create a Podman volume so that metadata persists across container restarts and updates:
```bash
podman volume create catalog-data
```

### 3. Run the Container
```bash
podman run -d \
  --name dataset-catalog \
  -p 5000:5000 \
  -v catalog-data:/data:Z \
  research-dataset-catalog:latest
```
> **Note on `:Z`**: The `:Z` flag ensures proper SELinux labeling for rootless Podman containers.

### 4. Verify Persistence
1. Open http://localhost:5000 in your browser.
2. Add a new dataset or edit an existing entry.
3. Stop and remove the container:
   ```bash
   podman stop dataset-catalog && podman rm dataset-catalog
   ```
4. Start a brand new container using the same volume:
   ```bash
   podman run -d --name dataset-catalog -p 5000:5000 -v catalog-data:/data:Z research-dataset-catalog:latest
   ```
5. Reload http://localhost:5000 — all your additions and edits are preserved!

### 5. Alternatively, using Podman Compose
```bash
podman compose up -d
```

---

## ☸️ OpenShift Deployment Guide

The `openshift/` directory contains standard Kubernetes/OpenShift declarative manifests.

### 1. Log in and Create a Project
```bash
oc login <cluster-url>
oc new-project dataset-catalog
```

### 2. Build or Import the Image
You can push your local image to the OpenShift internal registry or Quay/Docker Hub:
```bash
# Push to an external registry or OpenShift integrated registry
podman tag research-dataset-catalog:latest quay.io/<your-username>/research-dataset-catalog:latest
podman push quay.io/<your-username>/research-dataset-catalog:latest
```

*(Optional) Using OpenShift Binary Build directly from this directory:*
```bash
oc new-build --name research-dataset-catalog --binary --strategy=docker
oc start-build research-dataset-catalog --from-dir=. --follow
```

### 3. Apply the Manifests
Deploy the PersistentVolumeClaim (PVC), Deployment, Service, and Route:
```bash
oc apply -f openshift/catalog-all-in-one.yaml
```

Or apply individual files:
```bash
oc apply -f openshift/pvc.yaml
oc apply -f openshift/deployment.yaml
oc apply -f openshift/service.yaml
oc apply -f openshift/route.yaml
```

### 4. Obtain the Public Application URL
```bash
oc get route research-dataset-catalog -o jsonpath='{"https://"}{.spec.host}{"\n"}'
```

---

## 💻 Local Development (without Containers)

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
python3 app.py
```
Visit http://127.0.0.1:5000 in your web browser.

---

## 🧪 Automated Testing

A complete unit test suite is included in `tests/test_app.py`, verifying all CRUD operations, filtering by format/category/license, search, health checks, and database persistence:

```bash
python3 -m unittest discover tests
```

---

## 📁 Repository Structure

```text
.
├── app.py                     # Flask web application & route handlers
├── db.py                      # SQLite database access layer & schema initialization
├── requirements.txt           # Python application dependencies (Flask, Gunicorn)
├── Containerfile              # Container definition optimized for Podman & OpenShift
├── Dockerfile                 # Docker-compatible alias of Containerfile
├── compose.yaml               # Compose file for Podman Compose / Docker Compose
├── static/                    # CSS stylesheets, JavaScript, icons
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base layout with navbar and footer
│   ├── dashboard.html         # Overview dashboard & statistics
│   ├── datasets.html          # Searchable & filterable dataset catalog
│   ├── dataset_details.html   # Detailed metadata view
│   ├── dataset_form.html      # Add & edit dataset form
│   └── delete_dataset.html    # Confirmation dialog for dataset removal
├── tests/
│   └── test_app.py            # Automated unit tests
└── openshift/
    ├── catalog-all-in-one.yaml# Combined OpenShift deployment manifest
    ├── deployment.yaml        # Deployment specification
    ├── pvc.yaml               # PersistentVolumeClaim for /data
    ├── route.yaml             # OpenShift Route for public ingress
    └── service.yaml           # ClusterIP Service
```
