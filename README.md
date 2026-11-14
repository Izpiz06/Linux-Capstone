# Research Dataset Catalog

A simple Flask web application to manage research dataset metadata, built for Podman and OpenShift.

## Requirements Covered
- **Add / Edit / Remove** datasets (name, description, category, format, source URL, size, license).
- **List & Search** datasets.
- **Filter** by Format, Category, or License.
- **Persistence**: Metadata is stored in a SQLite database inside `/data`. Large datasets are kept external (referenced via URL), keeping the container lightweight.

---

## 1. Run with Podman

### Build Image
```bash
podman build -t dataset-catalog .
```

### Run with Persistent Volume
```bash
# Create volume for database persistence
podman volume create catalog-data

# Run container
podman run -d --name catalog -p 5000:5000 -v catalog-data:/data:Z dataset-catalog
```
Open **http://localhost:5000** in your browser.

---

## 2. Deploy to OpenShift

All OpenShift resources (PVC, Deployment, Service, Route) are in `openshift.yaml`.

```bash
oc apply -f openshift.yaml
```

Get your public URL:
```bash
oc get route dataset-catalog
```

---

## Project Structure
```text
├── app.py             # Entire Flask app + SQLite logic in one file
├── requirements.txt   # Just Flask
├── Containerfile      # Simple container build file
├── openshift.yaml     # OpenShift PVC, Deployment, Service & Route
├── templates/         # HTML pages
└── static/            # CSS & JS
```
