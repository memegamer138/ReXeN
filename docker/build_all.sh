#!/bin/sh
# Build and test-run all Docker containers for ReXeN tools

# Build images
docker build -f Dockerfile.httpx -t httpx-image .
docker build -f Dockerfile.gospider -t gospider-image .
docker build -f Dockerfile.katana -t katana-image .
docker build -f Dockerfile.subfinder -t subfinder-image .

# Test-run containers (prints help/version, then exits)
echo "Testing httpx-image..."
docker run --rm httpx-image httpx --version

echo "Testing gospider-image..."
docker run --rm gospider-image gospider --help

echo "Testing katana-image..."
docker run --rm katana-image katana --help

echo "Testing subfinder-image..."
docker run --rm subfinder-image subfinder --version