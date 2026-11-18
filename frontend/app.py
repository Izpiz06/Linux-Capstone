import os
from urllib.parse import urlparse
from flask import Flask, abort, flash, redirect, render_template, request, url_for
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-for-student-project"

BACKEND_URL = os.environ.get("BACKEND_URL", "http://catalog-backend:5001").rstrip("/")


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


def get_form_choices():
    """Fetch available categories and formats from backend."""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/datasets", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("categories", []), data.get("formats", [])
    except Exception:
        pass
    return [], []


@app.route("/healthz")
def healthz():
    return "OK", 200


@app.route("/")
def dashboard():
    try:
        resp = requests.get(f"{BACKEND_URL}/api/stats", timeout=5)
        data = resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        data = {"total_datasets": 0, "total_categories": 0, "total_formats": 0, "recent_datasets": []}

    return render_template(
        "dashboard.html",
        total_datasets=data.get("total_datasets", 0),
        total_categories=data.get("total_categories", 0),
        total_formats=data.get("total_formats", 0),
        recent_datasets=data.get("recent_datasets", []),
    )


@app.route("/datasets")
def datasets_catalog():
    search = request.args.get("search", request.args.get("q", "")).strip()
    category = request.args.get("category", "").strip()
    fmt = request.args.get("format", "").strip()
    lic = request.args.get("license", "").strip()

    params = {
        "search": search,
        "category": category,
        "format": fmt,
        "license": lic,
    }

    try:
        resp = requests.get(f"{BACKEND_URL}/api/datasets", params=params, timeout=5)
        data = resp.json() if resp.status_code == 200 else {}
    except Exception:
        data = {"datasets": [], "categories": [], "formats": [], "licenses": []}

    return render_template(
        "datasets.html",
        datasets=data.get("datasets", []),
        categories=data.get("categories", []),
        formats=data.get("formats", []),
        licenses=data.get("licenses", []),
        search_term=search,
        search=search,
        selected_category=category,
        selected_format=fmt,
        selected_license=lic,
    )


@app.route("/datasets/add", methods=["GET", "POST"])
def add_dataset():
    categories, formats = get_form_choices()

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

        try:
            resp = requests.post(f"{BACKEND_URL}/api/datasets", json=fields, timeout=5)
            if resp.status_code == 201:
                new_id = resp.json().get("id")
                flash("Dataset added successfully.", "success")
                return redirect(url_for("dataset_details", dataset_id=new_id))
            else:
                flash(resp.json().get("error", "Failed to add dataset"), "danger")
        except Exception as e:
            flash(f"Backend connection error: {e}", "danger")

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
    try:
        resp = requests.get(f"{BACKEND_URL}/api/datasets/{dataset_id}", timeout=5)
        if resp.status_code == 404:
            abort(404)
        dataset = resp.json()
    except Exception:
        abort(500)

    dataset["source_url"] = dataset.get("source", "")
    return render_template("dataset_details.html", dataset=dataset)


@app.route("/datasets/<int:dataset_id>/edit", methods=["GET", "POST"])
def edit_dataset(dataset_id):
    categories, formats = get_form_choices()
    try:
        resp = requests.get(f"{BACKEND_URL}/api/datasets/{dataset_id}", timeout=5)
        if resp.status_code == 404:
            abort(404)
        dataset = resp.json()
    except Exception:
        abort(500)

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

        try:
            put_resp = requests.put(f"{BACKEND_URL}/api/datasets/{dataset_id}", json=fields, timeout=5)
            if put_resp.status_code == 200:
                flash("Dataset updated successfully.", "success")
                return redirect(url_for("dataset_details", dataset_id=dataset_id))
            else:
                flash("Failed to update dataset", "danger")
        except Exception as e:
            flash(f"Backend connection error: {e}", "danger")

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
    try:
        resp = requests.get(f"{BACKEND_URL}/api/datasets/{dataset_id}", timeout=5)
        if resp.status_code == 404:
            abort(404)
        dataset = resp.json()
    except Exception:
        abort(500)

    if request.method == "POST":
        try:
            requests.delete(f"{BACKEND_URL}/api/datasets/{dataset_id}", timeout=5)
            flash("Dataset deleted successfully.", "success")
        except Exception as e:
            flash(f"Delete failed: {e}", "danger")
        return redirect(url_for("datasets_catalog"))

    return render_template("delete_dataset.html", dataset=dataset)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
