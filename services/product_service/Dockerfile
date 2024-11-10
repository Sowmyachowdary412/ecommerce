FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory with proper permissions
RUN mkdir -p /data/databases && \
    chmod -R 777 /data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]