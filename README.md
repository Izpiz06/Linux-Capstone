# Research Dataset Catalog

A simple Flask web application to manage research dataset metadata, containerized with **Podman**.

## Features & Requirements
- **Add / Edit / Remove** datasets (name, description, category, format, source URL, size, license).
- **List & Search** datasets.
- **Filter** by Format, Category, or License.
- **Persistence**: Metadata is stored in a SQLite database inside a mounted volume (`/data`). Datasets are referenced via URL so the container image remains lightweight.

---

## Running with Podman

### 1. Build the Image
```bash
podman build -t dataset-catalog .
```

### 2. Create a Persistent Volume
```bash
podman volume create catalog-data
```

### 3. Run the Container
```bash
podman run -d --name catalog -p 5000:5000 -v catalog-data:/data:Z dataset-catalog
```

Open **http://127.0.0.1:5000/** in your browser.

### 4. Stop and Remove Container
```bash
podman stop catalog
podman rm catalog
```

*(Your data remains safely stored in `catalog-data` and will reappear whenever you start a new container with the same volume).*

---

## Project Structure
```text
├── app.py             # Entire Flask app and SQLite persistence logic
├── requirements.txt   # Dependencies (Flask)
├── Containerfile      # Podman build definition
├── .containerignore   # Ignore files for Podman build
├── templates/         # HTML pages
└── static/            # CSS & JS styling
```
