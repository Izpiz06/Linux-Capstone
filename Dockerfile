# Use official lightweight Python runtime
FROM docker.io/library/python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DATA_DIR=/data

WORKDIR /app

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Support OpenShift arbitrary UID assignment:
# OpenShift runs containers with an assigned arbitrary UID belonging to group 0 (root).
# Grant group 0 read/write/execute permissions to both /app and /data directory.
RUN mkdir -p /data /app && \
    chgrp -R 0 /data /app && \
    chmod -R g+rwX /data /app

# Expose service port
EXPOSE 5000

# Declare persistent volume mount point for database metadata
VOLUME ["/data"]

# Default non-root user for local Podman/Docker execution
USER 1001

# Run with Gunicorn production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "app:app"]
