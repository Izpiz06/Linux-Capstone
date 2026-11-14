import os
import sqlite3
from datetime import date
from urllib.parse import urlparse
from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-for-student-project"

DATA_DIR = os.environ.get("DATA_DIR", ".")
DB_PATH = os.path.join(DATA_DIR, "catalog.db")

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
    """Connect to SQLite database."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create table and insert initial sample data if empty."""
    conn = get_db()
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
        )
        """
    )
    count = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    if count == 0:
        for ds in SAMPLE_DATASETS:
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
                    ds["source"],
                    ds["size"],
                    ds["license"],
                    ds["date_added"],
                ),
            )
        conn.commit()
    conn.close()


# Initialize database
init_db()


def get_dataset(dataset_id):
    """Fetch one dataset by ID or return 404."""
    conn = get_db()
    row = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    conn.close()
    if row is None:
        abort(404)
    data = dict(row)
    data["source_url"] = data.get("source", "")
    return data


def form_choices():
    """Get category and format choices for dropdowns."""
    conn = get_db()
    categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM datasets ORDER BY category")]
    formats = [r[0] for r in conn.execute("SELECT DISTINCT format FROM datasets ORDER BY format")]
    conn.close()
    return categories, formats


def validate_dataset_form():
    """Validate submitted fields."""
    source = request.form.get("source", request.form.get("source_url", "")).strip()
    fields = {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
        "category": request.form.get("category", "").strip(),
        "format": request.form.get("format", "").strip(),
        "source": source,
        "source_url": source,
        "size": request.form.get("size", "").strip(),
        "license": request.form.get("license", "").strip(),
    }
    errors = []

    required = ["name", "description", "category", "format", "size", "license"]
    for req in required:
        if not fields[req]:
            errors.append(f"{req.capitalize()} is required.")

    if fields["name"] and len(fields["name"]) < 3:
        errors.append("Dataset name must be at least 3 characters.")
    if fields["description"] and len(fields["description"]) < 10:
        errors.append("Description must be at least 10 characters.")

    if source:
        parsed = urlparse(source)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("Source URL must begin with http:// or https://")

    return fields, errors


@app.route("/healthz")
def healthz():
    """Health check for Podman/OpenShift."""
    return "OK", 200


@app.route("/")
def dashboard():
    conn = get_db()
    total_datasets = conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    total_categories = conn.execute("SELECT COUNT(DISTINCT category) FROM datasets").fetchone()[0]
    total_formats = conn.execute("SELECT COUNT(DISTINCT format) FROM datasets").fetchone()[0]
    recent_rows = conn.execute("SELECT * FROM datasets ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()

    recent_datasets = [dict(r) for r in recent_rows]
    for d in recent_datasets:
        d["source_url"] = d.get("source", "")

    return render_template(
        "dashboard.html",
        total_datasets=total_datasets,
        total_categories=total_categories,
        total_formats=total_formats,
        recent_datasets=recent_datasets,
    )


@app.route("/datasets")
def datasets_catalog():
    search = request.args.get("search", request.args.get("q", "")).strip()
    selected_category = request.args.get("category", "").strip()
    selected_format = request.args.get("format", "").strip()
    selected_license = request.args.get("license", "").strip()

    query = "SELECT * FROM datasets WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if selected_category:
        query += " AND category = ?"
        params.append(selected_category)
    if selected_format:
        query += " AND format = ?"
        params.append(selected_format)
    if selected_license:
        query += " AND license = ?"
        params.append(selected_license)

    query += " ORDER BY id DESC"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM datasets ORDER BY category")]
    formats = [r[0] for r in conn.execute("SELECT DISTINCT format FROM datasets ORDER BY format")]
    licenses = [r[0] for r in conn.execute("SELECT DISTINCT license FROM datasets ORDER BY license")]
    conn.close()

    filtered_datasets = [dict(r) for r in rows]
    for d in filtered_datasets:
        d["source_url"] = d.get("source", "")

    return render_template(
        "datasets.html",
        datasets=filtered_datasets,
        categories=categories,
        formats=formats,
        licenses=licenses,
        search_term=search,
        search=search,
        selected_category=selected_category,
        selected_format=selected_format,
        selected_license=selected_license,
    )


@app.route("/datasets/add", methods=["GET", "POST"])
def add_dataset():
    categories, formats = form_choices()
    if request.method == "POST":
        fields, errors = validate_dataset_form()
        if errors:
            for error in errors:
                flash(error, "danger")
            return (
                render_template(
                    "dataset_form.html",
                    dataset=fields,
                    page_title="Add Dataset",
                    is_edit=False,
                    categories=categories,
                    formats=formats,
                ),
                400,
            )

        conn = get_db()
        cursor = conn.execute(
            """
            INSERT INTO datasets (name, description, category, format, source, size, license, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["name"],
                fields["description"],
                fields["category"],
                fields["format"],
                fields["source"],
                fields["size"],
                fields["license"],
                date.today().isoformat(),
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        flash("Dataset added successfully.", "success")
        return redirect(url_for("dataset_details", dataset_id=new_id))

    return render_template(
        "dataset_form.html",
        dataset={},
        page_title="Add Dataset",
        is_edit=False,
        categories=categories,
        formats=formats,
    )


@app.route("/datasets/<int:dataset_id>")
def dataset_details(dataset_id):
    return render_template("dataset_details.html", dataset=get_dataset(dataset_id))


@app.route("/datasets/<int:dataset_id>/edit", methods=["GET", "POST"])
def edit_dataset(dataset_id):
    dataset = get_dataset(dataset_id)
    categories, formats = form_choices()

    if request.method == "POST":
        fields, errors = validate_dataset_form()
        if errors:
            for error in errors:
                flash(error, "danger")
            return (
                render_template(
                    "dataset_form.html",
                    dataset={**dataset, **fields},
                    page_title="Edit Dataset",
                    is_edit=True,
                    categories=categories,
                    formats=formats,
                ),
                400,
            )

        conn = get_db()
        conn.execute(
            """
            UPDATE datasets
            SET name = ?, description = ?, category = ?, format = ?, source = ?, size = ?, license = ?
            WHERE id = ?
            """,
            (
                fields["name"],
                fields["description"],
                fields["category"],
                fields["format"],
                fields["source"],
                fields["size"],
                fields["license"],
                dataset_id,
            ),
        )
        conn.commit()
        conn.close()

        flash("Dataset updated successfully.", "success")
        return redirect(url_for("dataset_details", dataset_id=dataset_id))

    return render_template(
        "dataset_form.html",
        dataset=dataset,
        page_title="Edit Dataset",
        is_edit=True,
        categories=categories,
        formats=formats,
    )


@app.route("/datasets/<int:dataset_id>/delete", methods=["GET", "POST"])
def delete_dataset(dataset_id):
    dataset = get_dataset(dataset_id)
    if request.method == "POST":
        conn = get_db()
        conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        conn.commit()
        conn.close()
        flash("Dataset deleted successfully.", "success")
        return redirect(url_for("datasets_catalog"))
    return render_template("delete_dataset.html", dataset=dataset)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
