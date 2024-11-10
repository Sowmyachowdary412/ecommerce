FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Configure Streamlit
RUN mkdir -p /root/.streamlit
RUN echo "\
[server]\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
" > /root/.streamlit/config.toml

CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0"]