FROM python:3.11-slim

WORKDIR /app

# Node/npm are installed so the ESLint-based JS/TS static analysis
# (services/eslint_service.py, invoked via npx) works inside the container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads reports

ENV PORT=5000
EXPOSE 5000

CMD gunicorn app:app --preload --bind 0.0.0.0:$PORT --workers 2 --timeout 120
