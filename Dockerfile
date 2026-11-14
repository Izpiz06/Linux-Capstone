FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directory for persistent database (writable by OpenShift)
RUN mkdir -p /data && chmod 777 /data

ENV DATA_DIR=/data
EXPOSE 5000

CMD ["python", "app.py"]
