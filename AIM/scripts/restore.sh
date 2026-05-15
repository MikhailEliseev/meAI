#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <timestamp>"
    echo "Example: $0 20260515_052000"
    exit 1
fi

TIMESTAMP=$1
BACKUP_DIR="./backups"

echo "Restoring from backup: $TIMESTAMP"

# 1. Stop services
echo "Stopping services..."
docker-compose down

# 2. Restore database
echo "Restoring database..."
gunzip -c "$BACKUP_DIR/aim_db_$TIMESTAMP.db.gz" > data/production/aim.db
echo "Database restored"

# 3. Restore configurations
echo "Restoring configurations..."
tar -xzf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz"
echo "Configurations restored"

# 4. Restore vaults
echo "Restoring Obsidian vaults..."
tar -xzf "$BACKUP_DIR/vaults_$TIMESTAMP.tar.gz"
echo "Vaults restored"

# 5. Start services
echo "Starting services..."
docker-compose up -d

# 6. Verify health
echo "Waiting for services to start..."
sleep 10
curl -f http://localhost/health || echo "Warning: Health check failed"

echo "Restore completed!"
