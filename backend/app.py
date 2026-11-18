import os
import time
from datetime import date
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "catalog-db")
DB_NAME = os.environ.get("DB_NAME", "catalog")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_PORT = int(os.environ.get("DB_PORT", 5432))

SAMPLE_DATASETS = [
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
    """Get a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )


def init_db():
    """Wait for database to be ready, create schema, and seed initial data."""
    retries = 15
    conn = None
    while retries > 0:
        try:
            conn = get_db()
            break
        except Exception as e:
            print(f"Waiting for database to accept connections... ({e})")
            retries -= 1
            time.sleep(2)

    if not conn:
        raise RuntimeError("Failed to connect to PostgreSQL database.")

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    format VARCHAR(50) NOT NULL,
                    source TEXT,
                    size VARCHAR(50) NOT NULL,
                    license VARCHAR(100) NOT NULL,
                    date_added VARCHAR(20) NOT NULL
                );
                """
            )
            cur.execute("SELECT COUNT(*) FROM datasets;")
            count = cur.fetchone()[0]
            if count == 0:
                for ds in SAMPLE_DATASETS:
                    cur.execute(
                        """
                        INSERT INTO datasets (name, description, category, format, source, size, license, date_added)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (
                            ds["name"],
                            ds["description"],
                            ds["category"],
                            ds["format"],
                            ds["source"],
                            ds["size"],
                            ds["license"],
                            ds["date_added"],
                        ),
                    )
    conn.close()
    print("Database initialization complete.")


# Initialize DB
init_db()


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/stats")
def stats():
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS total_datasets FROM datasets;")
            total_datasets = cur.fetchone()["total_datasets"]

            cur.execute("SELECT COUNT(DISTINCT category) AS total_categories FROM datasets;")
            total_categories = cur.fetchone()["total_categories"]

            cur.execute("SELECT COUNT(DISTINCT format) AS total_formats FROM datasets;")
            total_formats = cur.fetchone()["total_formats"]

            cur.execute("SELECT * FROM datasets ORDER BY id DESC LIMIT 5;")
            recent_datasets = cur.fetchall()

    return jsonify(
        {
            "total_datasets": total_datasets,
            "total_categories": total_categories,
            "total_formats": total_formats,
            "recent_datasets": recent_datasets,
        }
    )


@app.route("/api/datasets", methods=["GET"])
def list_datasets():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    fmt = request.args.get("format", "").strip()
    lic = request.args.get("license", "").strip()

    query = "SELECT * FROM datasets WHERE 1=1"
    params = []

    if search:
        query += " AND (name ILIKE %s OR description ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category:
        query += " AND category = %s"
        params.append(category)
    if fmt:
        query += " AND format = %s"
        params.append(fmt)
    if lic:
        query += " AND license = %s"
        params.append(lic)

    query += " ORDER BY id DESC;"

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            datasets = cur.fetchall()

            cur.execute("SELECT DISTINCT category FROM datasets ORDER BY category;")
            categories = [r["category"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT format FROM datasets ORDER BY format;")
            formats = [r["format"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT license FROM datasets ORDER BY license;")
            licenses = [r["license"] for r in cur.fetchall()]

    return jsonify(
        {
            "datasets": datasets,
            "categories": categories,
            "formats": formats,
            "licenses": licenses,
        }
    )


@app.route("/api/datasets/<int:dataset_id>", methods=["GET"])
def get_dataset(dataset_id):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM datasets WHERE id = %s;", (dataset_id,))
            dataset = cur.fetchone()

    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    return jsonify(dataset)


@app.route("/api/datasets", methods=["POST"])
def create_dataset():
    data = request.get_json(force=True)
    required = ["name", "description", "category", "format", "size", "license"]
    for req in required:
        if not data.get(req):
            return jsonify({"error": f"{req} is required"}), 400

    date_added = data.get("date_added", date.today().isoformat())
    source = data.get("source", "").strip()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO datasets (name, description, category, format, source, size, license, date_added)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
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
            new_id = cur.fetchone()[0]

    return jsonify({"id": new_id, "message": "Dataset added successfully"}), 201


@app.route("/api/datasets/<int:dataset_id>", methods=["PUT"])
def update_dataset(dataset_id):
    data = request.get_json(force=True)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE datasets
                SET name = %s, description = %s, category = %s, format = %s, source = %s, size = %s, license = %s
                WHERE id = %s;
                """,
                (
                    data["name"],
                    data["description"],
                    data["category"],
                    data["format"],
                    data.get("source", ""),
                    data["size"],
                    data["license"],
                    dataset_id,
                ),
            )
    return jsonify({"message": "Dataset updated successfully"})


@app.route("/api/datasets/<int:dataset_id>", methods=["DELETE"])
def delete_dataset(dataset_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM datasets WHERE id = %s;", (dataset_id,))
    return jsonify({"message": "Dataset deleted successfully"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
