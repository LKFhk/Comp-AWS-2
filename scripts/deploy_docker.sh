#!/bin/bash
set -e

echo "Building and deploying Docker containers..."

# Build images
docker-compose build

# Deploy services
docker-compose --profile prod up -d

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 30

# Verify deployment
curl -f http://localhost:8001/health || exit 1

echo "Docker deployment completed successfully"
