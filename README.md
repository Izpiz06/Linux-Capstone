# Research Dataset Catalog

A 3-tier containerized web application to maintain and search metadata about student research datasets. Built using **Podman**, with custom Containerfiles, persistent storage, and an isolated container network.

---

## 🎯 Features & Requirements

- **Add Dataset**: Name, description, category, format, source URL, size, and license.
- **Search & List**: Real-time keyword search across dataset names and descriptions.
- **Filter (Assigned Variation)**: Filter by **Format**, **Category**, or **License**.
- **Edit & Delete**: Full catalog entry modification and removal.
- **Persistent Storage**: PostgreSQL data is stored on a persistent named Podman volume (`catalog-db-data`).
- **Zero Dataset Bloat**: Actual dataset files are referenced by URL, keeping container images small and fast.

---

## 🏗️ Architecture

```text
[ Host Browser (http://localhost:5000) ]
                   │  Port mapping (-p 5000:5000)
                   ▼
         ┌──────────────────┐
         │ catalog-frontend │  (Custom Containerfile: Flask Web UI)
         └────────┬─────────┘
                  │  HTTP (catalog-net)
                  ▼
         ┌──────────────────┐
         │ catalog-backend  │  (Custom Containerfile: Flask REST API)
         └────────┬─────────┘
                  │  PostgreSQL TCP 5432 (catalog-net)
                  ▼
         ┌──────────────────┐
         │    catalog-db    │  (PostgreSQL 15 Container)
         └────────┬─────────┘
                  │  Mounts volume
                  ▼
        [ catalog-db-data ]    <-- Named Podman Volume (Persistence)
```

---

## 🚀 Step-by-Step Commands for Live Demonstration

### Step 1: Create Podman Network & Persistent Volume
```bash
# 1. Create a dedicated bridge network for container-to-container DNS
podman network create catalog-net

# 2. Create persistent volume for PostgreSQL database
podman volume create catalog-db-data
```

### Step 2: Start the Database Container
```bash
podman run -d --name catalog-db \
  --network catalog-net \
  -e POSTGRES_DB=catalog \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -v catalog-db-data:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:15-alpine
```

### Step 3: Build & Run Backend API Container
```bash
# Build custom image
podman build -t catalog-backend ./backend

# Run container on the common network
podman run -d --name catalog-backend \
  --network catalog-net \
  -e DB_HOST=catalog-db \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  -e DB_NAME=catalog \
  catalog-backend
```

### Step 4: Build & Run Frontend UI Container
```bash
# Build custom image
podman build -t catalog-frontend ./frontend

# Run container with port mapping to host (port 5000)
podman run -d --name catalog-frontend \
  --network catalog-net \
  -p 5000:5000 \
  -e BACKEND_URL=http://catalog-backend:5001 \
  catalog-frontend
```

---

## 🌐 Accessing the Application

Open your browser and navigate to:
**http://localhost:5000**

You can:
1. Browse existing sample datasets on the dashboard.
2. Click **Add Dataset** to register a new dataset.
3. Search by name or description in **Dataset Catalog**.
4. Filter by **Format**, **Category**, or **License**.
5. Edit or Delete any entry.

---

## 🔍 Verification & Container Management

### Check running containers:
```bash
podman ps
```

### Inspect logs of any container:
```bash
podman logs catalog-frontend
podman logs catalog-backend
podman logs catalog-db
```

### Inspect the Podman network:
```bash
podman network inspect catalog-net
```

### Verify Persistence Across Container Restarts:
1. Add a new dataset in the web browser.
2. Stop and delete the database container:
   ```bash
   podman stop catalog-db && podman rm catalog-db
   ```
3. Re-launch the database container with the same volume:
   ```bash
   podman run -d --name catalog-db --network catalog-net \
     -e POSTGRES_DB=catalog -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
     -v catalog-db-data:/var/lib/postgresql/data:Z \
     docker.io/library/postgres:15-alpine
   ```
4. Refresh http://localhost:5000 — all your data is preserved!

---

## 🛑 Clean Up Everything
```bash
podman stop catalog-frontend catalog-backend catalog-db
podman rm catalog-frontend catalog-backend catalog-db
podman volume rm catalog-db-data
podman network rm catalog-net
```

---

## 🎓 Faculty Evaluation / Viva Talking Points

1. **Why 3 containers?**
   - Separation of concerns: UI layer (frontend), business logic and REST API (backend), and data storage (database) run independently.
2. **How do containers communicate?**
   - Through the user-defined `catalog-net` network using Podman’s built-in DNS. The frontend talks to `http://catalog-backend:5001` and the backend talks to `catalog-db:5432` without hardcoding IP addresses.
3. **What is the `:Z` flag on the volume mount?**
   - It configures SELinux context so rootless Podman has read/write permissions on the volume directory.
4. **How are dataset sizes managed without bloating images?**
   - We store only metadata (name, format, size, license, source URL) in PostgreSQL. The large raw datasets reside at external source URLs.
