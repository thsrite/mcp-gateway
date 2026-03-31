# Stage 1: Build frontend
FROM node:alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml config.yaml.example ./
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir . && \
    mv config.yaml.example config.yaml && \
    mkdir -p data/repos

COPY app/ ./app/
COPY run.py ./
COPY --from=frontend-build /build/dist ./frontend/dist/

VOLUME /app/data
EXPOSE 9000 9001
CMD ["python", "run.py"]
