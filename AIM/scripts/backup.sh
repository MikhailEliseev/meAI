#!/bin/bash
set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting backup at $TIMESTAMP..."

# 1. Backup database
echo "Backing up database..."
if [ -f "data/production/aim.db" ]; then
    sqlite3 data/production/aim.db ".backup '$BACKUP_DIR/aim_db_$TIMESTAMP.db'"
    gzip "$BACKUP_DIR/aim_db_$TIMESTAMP.db"
    echo "Database backup: $BACKUP_DIR/aim_db_$TIMESTAMP.db.gz"
fi

# 2. Backup configurations
echo "Backing up configurations..."
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
    .env.production \
    docker-compose.yml \
    nginx.conf \
    prometheus.yml \
    prometheus-alerts.yml \
    grafana/

echo "Config backup: $BACKUP_DIR/config_$TIMESTAMP.tar.gz"

# 3. Backup Obsidian vaults
echo "Backing up Obsidian vaults..."
tar -czf "$BACKUP_DIR/vaults_$TIMESTAMP.tar.gz" obsidian/
echo "Vaults backup: $BACKUP_DIR/vaults_$TIMESTAMP.tar.gz"

# 4. Backup logs (last 7 days)
echo "Backing up recent logs..."
if [ -d "logs" ]; then
    find logs/ -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" {} + 2>/dev/null || echo "No recent logs found"
    echo "Logs backup: $BACKUP_DIR/logs_$TIMESTAMP.tar.gz"
fi

# 5. Create backup manifest
cat > "$BACKUP_DIR/manifest_$TIMESTAMP.txt" <<EOF
Backup created: $TIMESTAMP
Database: aim_db_$TIMESTAMP.db.gz
Config: config_$TIMESTAMP.tar.gz
Vaults: vaults_$TIMESTAMP.tar.gz
Logs: logs_$TIMESTAMP.tar.gz
EOF

# 6. Clean old backups (older than retention period)
echo "Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.txt" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"
ls -lh "$BACKUP_DIR" | tail -10
