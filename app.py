import os
from datetime import date
from urllib.parse import urlparse

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for

import db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dataset-catalog-insecure-secret-key-change-in-production"
)

# Initialize database schema and default dataset records
with app.app_context():
    db.init_db()


def get_dataset(dataset_id):
    """Return one dataset by ID, or raise a 404 for an unknown ID."""
    dataset = db.get_dataset(dataset_id)
    if dataset is None:
        abort(404)
    return dataset


def form_choices():
    """Build form choices from the current catalog records."""
    categories = db.get_categories()
    formats = db.get_formats()
    return categories, formats


def validate_dataset_form():
    """Validate submitted fields and return normalized data plus errors."""
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

    required_fields = {
        "name": "Dataset name",
        "description": "Description",
        "category": "Category",
        "format": "Format",
        "size": "Dataset size",
        "license": "License information",
    }
    for field, label in required_fields.items():
        if not fields[field]:
            errors.append(f"{label} is required.")

    if fields["name"] and len(fields["name"]) < 3:
        errors.append("Dataset name must be at least 3 characters.")
    if fields["description"] and len(fields["description"]) < 10:
        errors.append("Description must be at least 10 characters.")

    if source:
        parsed_url = urlparse(source)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            errors.append("Enter a valid source URL beginning with http:// or https://.")

    return fields, errors


@app.route("/healthz")
@app.route("/health")
def health_check():
    """Kubernetes / OpenShift readiness and liveness probe endpoint."""
    try:
        # Verify database accessibility
        db.get_stats()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/")
def dashboard():
    stats = db.get_stats()
    recent_datasets = db.get_recent_datasets(5)
    return render_template(
        "dashboard.html",
        total_datasets=stats["total_datasets"],
        total_categories=stats["total_categories"],
        total_formats=stats["total_formats"],
        recent_datasets=recent_datasets,
    )


@app.route("/datasets")
def datasets_catalog():
    search_term = request.args.get("search", request.args.get("q", "")).strip()
    selected_category = request.args.get("category", "").strip()
    selected_format = request.args.get("format", "").strip()
    selected_license = request.args.get("license", "").strip()

    filtered_datasets = db.get_all_datasets(
        search=search_term,
        category=selected_category,
        format=selected_format,
        license=selected_license,
    )

    return render_template(
        "datasets.html",
        datasets=filtered_datasets,
        categories=db.get_categories(),
        formats=db.get_formats(),
        licenses=db.get_licenses(),
        search_term=search_term,
        search=search_term,
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

        fields["date_added"] = date.today().isoformat()
        dataset_id = db.add_dataset(fields)
        flash("Dataset added successfully.", "success")
        return redirect(url_for("dataset_details", dataset_id=dataset_id))

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

        db.update_dataset(dataset_id, fields)
        flash("Dataset changes saved successfully.", "success")
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
        db.delete_dataset(dataset_id)
        flash("Dataset deleted successfully.", "success")
        return redirect(url_for("datasets_catalog"))
    return render_template("delete_dataset.html", dataset=dataset)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
