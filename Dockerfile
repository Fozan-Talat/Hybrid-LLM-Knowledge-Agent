FROM python:3.11-slim

# ----------------------------
# System dependencies
# ----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Working directory
# ----------------------------
WORKDIR /app

# ----------------------------
# Python dependencies
# ----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
# spaCy model (explicit install)
# ----------------------------
RUN python -m spacy download en_core_web_sm

# ----------------------------
# Application code
# ----------------------------
COPY . .

# ----------------------------
# Environment
# ----------------------------
ENV PYTHONUNBUFFERED=1

# ----------------------------
# Expose API
# ----------------------------
EXPOSE 8000

# ----------------------------
# Run API
# ----------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
