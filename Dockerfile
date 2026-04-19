# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Stage 2: install dependencies ─────────────────────────────────────────────
# Copy only requirements first so Docker can cache this layer
# (if requirements.txt hasn't changed, this layer is reused on rebuild)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 3: copy application code ────────────────────────────────────────────
COPY . .

# ── Stage 4: expose port and run ──────────────────────────────────────────────
EXPOSE 8000

# Run database migrations then start the server
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000
