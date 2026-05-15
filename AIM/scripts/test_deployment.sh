#!/bin/bash
set -e

echo "=== AIM Deployment Test ==="
echo ""

# Build containers
echo "Building containers..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Test app health
echo "Testing app health..."
curl -f http://localhost:8000/health || exit 1
echo "✓ App health check passed"

# Test app readiness
echo "Testing app readiness..."
curl -f http://localhost:8000/ready || exit 1
echo "✓ App readiness check passed"

# Test redis
echo "Testing redis..."
docker-compose exec -T redis redis-cli ping | grep PONG || exit 1
echo "✓ Redis check passed"

# Test nginx
echo "Testing nginx..."
curl -f http://localhost/health || exit 1
echo "✓ Nginx check passed"

# Test prometheus
echo "Testing prometheus..."
curl -f http://localhost:9090/-/healthy || exit 1
echo "✓ Prometheus check passed"

# Test grafana
echo "Testing grafana..."
curl -f http://localhost:3000/api/health || exit 1
echo "✓ Grafana check passed"

# Check all containers running
echo "Checking container status..."
docker-compose ps | grep -v "Exit" || exit 1
echo "✓ All containers running"

echo ""
echo "=== All tests passed! ==="
echo ""
echo "Services:"
echo "  App:        http://localhost:8000"
echo "  Nginx:      http://localhost"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000"
