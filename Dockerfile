# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

# Install git (needed for cloning MCP servers)
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ ./app/
COPY run.py ./

# Copy built frontend
COPY --from=frontend-build /build/dist ./frontend/dist/

# Copy default config (user can mount their own)
COPY config.yaml.example ./config.yaml

# Data directory for SQLite DB and cloned repos
RUN mkdir -p data/repos
VOLUME /app/data

# Web UI port + MCP endpoint port
EXPOSE 9000 9001

CMD ["python", "run.py"]
