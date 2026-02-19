#!/bin/sh
# Build all Docker containers for ReXeN tools

docker build -f Dockerfile.waybackurls -t waybackurls-image .
docker build -f Dockerfile.gau -t gau-image .
docker build -f Dockerfile.httpx -t httpx-image .
# Add more build commands below as you add new tools
