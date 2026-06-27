#!/bin/bash
set -e

echo "🚀 Starting deployment to production server..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVER="aim"
PROJECT_DIR="/opt/aim/AIM"
SERVICE="frontend"

# Step 1: Pull latest code
echo -e "${YELLOW}📥 Step 1: Pulling latest code from GitHub...${NC}"
ssh $SERVER "cd $PROJECT_DIR && git fetch origin && git reset --hard origin/main"
echo -e "${GREEN}✓ Code updated${NC}"

# Step 2: Rebuild frontend container
echo -e "${YELLOW}🔨 Step 2: Rebuilding frontend Docker image...${NC}"
ssh $SERVER "cd $PROJECT_DIR && docker compose build $SERVICE"
echo -e "${GREEN}✓ Frontend rebuilt${NC}"

# Step 3: Restart frontend service
echo -e "${YELLOW}🔄 Step 3: Restarting frontend service...${NC}"
ssh $SERVER "cd $PROJECT_DIR && docker compose up -d $SERVICE"
echo -e "${GREEN}✓ Frontend restarted${NC}"

# Step 4: Wait for health check
echo -e "${YELLOW}🏥 Step 4: Waiting for health check...${NC}"
sleep 10
HEALTH=$(ssh $SERVER "docker ps --filter name=aim-$SERVICE --format '{{.Status}}'" | grep -o "healthy" || echo "unhealthy")

if [ "$HEALTH" == "healthy" ]; then
    echo -e "${GREEN}✓ Service is healthy${NC}"
else
    echo -e "${RED}⚠ Warning: Service health check pending${NC}"
    echo "Check logs with: ssh $SERVER 'docker logs aim-$SERVICE --tail 50'"
fi

# Step 5: Show deployment info
echo -e "${YELLOW}📊 Deployment Summary:${NC}"
ssh $SERVER "cd $PROJECT_DIR && git log -1 --oneline"
ssh $SERVER "docker ps --filter name=aim-$SERVICE --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo "🌐 Check: https://iamaim.ru"
