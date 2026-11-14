import os
import sqlite3
from datetime import date

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.environ.get("DATA_DIR", "."), "catalog.db"),
)

INITIAL_DATASETS = [
    {
        "name": "Global Climate Indicators",
        "description": "A curated collection of climate observations and indicators for long-term environmental research.",
        "category": "Climate Science",
        "format": "CSV",
        "source": "https://example.com/climate-indicators",
        "size": "2.4 GB",
        "license": "CC BY 4.0",
        "date_added": "2026-10-28",
    },
    {
        "name": "Urban Mobility Survey",
        "description": "Anonymized travel patterns and transport preferences from a multi-city survey.",
        "category": "Social Science",
        "format": "XLSX",
        "source": "https://example.com/urban-mobility",
        "size": "860 MB",
        "license": "CC BY-NC 4.0",
        "date_added": "2026-10-21",
    },
    {
        "name": "Biodiversity Field Observations",
        "description": "Species observations recorded across protected habitats during field studies.",
        "category": "Biology",
        "format": "JSON",
        "source": "https://example.com/biodiversity",
        "size": "1.1 GB",
        "license": "Public Domain",
        "date_added": "2026-10-12",
    },
    {
        "name": "Open Materials Measurements",
        "description": "Laboratory measurements of material properties from reproducible experiments.",
        "category": "Materials Science",
        "format": "Parquet",
        "source": "https://example.com/materials",
        "size": "540 MB",
        "license": "CC BY 4.0",
        "date_added": "2026-09-30",
    },
]


def get_db():
    """Create and return a database connection."""
    db_path = os.environ.get(
        "DATABASE_PATH",
        os.path.join(os.environ.get("DATA_DIR", "."), "catalog.db"),
    )
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize tables and seed with initial data if empty."""
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                format TEXT NOT NULL,
                source TEXT,
                size TEXT NOT NULL,
                license TEXT NOT NULL,
                date_added TEXT NOT NULL
            );
            """
        )
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
        if count == 0:
            for ds in INITIAL_DATASETS:
                conn.execute(
                    """
                    INSERT INTO datasets (name, description, category, format, source, size, license, date_added)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ds["name"],
                        ds["description"],
                        ds["category"],
                        ds["format"],
                        ds.get("source") or ds.get("source_url", ""),
                        ds["size"],
                        ds["license"],
                        ds["date_added"],
                    ),
                )
            conn.commit()
    finally:
        conn.close()


def get_dataset(dataset_id):
    """Retrieve a single dataset by ID, returned as a dict."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["source_url"] = data.get("source", "")
        return data
    finally:
        conn.close()


def get_all_datasets(search=None, category=None, format=None, license=None):
    """Retrieve datasets with optional search and filters."""
    query = "SELECT * FROM datasets WHERE 1=1"
    params = []

    if search:
        search_pattern = f"%{search}%"
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([search_pattern, search_pattern])

    if category:
        query += " AND category = ?"
        params.append(category)

    if format:
        query += " AND format = ?"
        params.append(format)

    if license:
        query += " AND license = ?"
        params.append(license)

    query += " ORDER BY id DESC"

    conn = get_db()
    try:
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["source_url"] = d.get("source", "")
            result.append(d)
        return result
    finally:
        conn.close()


def get_recent_datasets(limit=5):
    """Get most recently added datasets."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM datasets ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["source_url"] = d.get("source", "")
            result.append(d)
        return result
    finally:
        conn.close()


def get_categories():
    """Get distinct categories sorted."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT category FROM datasets WHERE category != '' ORDER BY category ASC"
        ).fetchall()
        return [r["category"] for r in rows]
    finally:
        conn.close()


def get_formats():
    """Get distinct formats sorted."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT format FROM datasets WHERE format != '' ORDER BY format ASC"
        ).fetchall()
        return [r["format"] for r in rows]
    finally:
        conn.close()


def get_licenses():
    """Get distinct licenses sorted."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT license FROM datasets WHERE license != '' ORDER BY license ASC"
        ).fetchall()
        return [r["license"] for r in rows]
    finally:
        conn.close()


def add_dataset(data):
    """Add a new dataset and return its new ID."""
    source = data.get("source") or data.get("source_url", "")
    date_added = data.get("date_added", date.today().isoformat())
    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO datasets (name, description, category, format, source, size, license, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["description"],
                data["category"],
                data["format"],
                source,
                data["size"],
                data["license"],
                date_added,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_dataset(dataset_id, data):
    """Update an existing dataset."""
    source = data.get("source") or data.get("source_url", "")
    conn = get_db()
    try:
        conn.execute(
            """
            UPDATE datasets
            SET name = ?, description = ?, category = ?, format = ?, source = ?, size = ?, license = ?
            WHERE id = ?
            """,
            (
                data["name"],
                data["description"],
                data["category"],
                data["format"],
                source,
                data["size"],
                data["license"],
                dataset_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_dataset(dataset_id):
    """Delete a dataset by ID."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        conn.commit()
    finally:
        conn.close()


def get_stats():
    """Return catalog statistics (total_datasets, total_categories, total_formats)."""
    conn = get_db()
    try:
        total_datasets = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
        total_categories = conn.execute(
            "SELECT COUNT(DISTINCT category) FROM datasets WHERE category != ''"
        ).fetchone()[0]
        total_formats = conn.execute(
            "SELECT COUNT(DISTINCT format) FROM datasets WHERE format != ''"
        ).fetchone()[0]
        return {
            "total_datasets": total_datasets,
            "total_categories": total_categories,
            "total_formats": total_formats,
        }
    finally:
        conn.close()
