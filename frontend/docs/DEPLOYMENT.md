# Deployment Guide

## Overview

This guide covers deploying the Linear integration frontend with WebSocket support.

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- Linear API key and webhook secret
- NextAuth configuration
- Domain with SSL/TLS certificate (for production)

## Environment Variables

Create `.env.local` file:

```bash
# Linear API
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
LINEAR_WEBHOOK_SECRET=your_webhook_secret_here

# NextAuth
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your_nextauth_secret_here

# Database (if using)
DATABASE_URL=postgresql://user:password@host:5432/database

# Optional
NODE_ENV=production
PORT=3000
```

## Local Development

### 1. Install Dependencies

```bash
npm install
```

### 2. Setup Environment

```bash
cp .env.example .env.local
# Edit .env.local with your values
```

### 3. Run Development Server

```bash
npm run dev
```

Server starts at http://localhost:3000

### 4. Test WebSocket Connection

Open browser console and check for:
```
[WebSocket] Connecting to ws://localhost:3000
[WebSocket] Connected
```

## Production Deployment

### Option 1: Vercel (Recommended for Next.js)

**Note:** Vercel doesn't support WebSocket connections. Use Option 2 or 3 for WebSocket support.

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables
vercel env add LINEAR_API_KEY
vercel env add LINEAR_WEBHOOK_SECRET
vercel env add NEXTAUTH_SECRET
```

**Limitations:**
- No WebSocket support (serverless functions)
- Use polling or Server-Sent Events instead

### Option 2: VPS/Dedicated Server (Full WebSocket Support)

#### Requirements
- Ubuntu 20.04+ or similar
- Node.js 18+
- nginx (reverse proxy)
- PM2 (process manager)
- SSL certificate (Let's Encrypt)

#### 1. Setup Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2
sudo npm install -g pm2

# Install nginx
sudo apt install -y nginx

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

#### 2. Clone and Build

```bash
# Clone repository
git clone https://github.com/your-repo/frontend.git
cd frontend

# Install dependencies
npm install

# Build production
npm run build
```

#### 3. Configure PM2

Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'linear-frontend',
    script: 'server.ts',
    interpreter: 'node',
    interpreter_args: '--loader tsx',
    instances: 1, // Single instance for WebSocket
    exec_mode: 'fork', // Fork mode for WebSocket
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  }]
};
```

Start with PM2:

```bash
# Start application
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

#### 4. Configure nginx

Create `/etc/nginx/sites-available/linear-frontend`:

```nginx
upstream linear_backend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://linear_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://linear_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Static files caching
    location /_next/static {
        proxy_pass http://linear_backend;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/linear-frontend /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

#### 5. Setup SSL with Let's Encrypt

```bash
# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

#### 6. Configure Firewall

```bash
# Allow HTTP, HTTPS, SSH
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### Option 3: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - LINEAR_API_KEY=${LINEAR_API_KEY}
      - LINEAR_WEBHOOK_SECRET=${LINEAR_WEBHOOK_SECRET}
      - NEXTAUTH_URL=${NEXTAUTH_URL}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

#### 3. Deploy

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Linear Webhook Configuration

### 1. Create Webhook in Linear

1. Go to Linear Settings → API → Webhooks
2. Click "Create webhook"
3. Configure:
   - **URL**: `https://your-domain.com/api/webhooks/linear`
   - **Secret**: Generate strong secret (save to `LINEAR_WEBHOOK_SECRET`)
   - **Events**: Select `Issue`, `Project`, `Comment`
4. Save webhook

### 2. Test Webhook

```bash
# Send test webhook
curl -X POST https://your-domain.com/api/webhooks/linear \
  -H "Content-Type: application/json" \
  -H "linear-signature: YOUR_SIGNATURE" \
  -d '{
    "action": "create",
    "type": "Issue",
    "data": {
      "id": "test-1",
      "title": "Test Task"
    },
    "organizationId": "org-1",
    "webhookTimestamp": 1234567890,
    "webhookId": "webhook-1"
  }'
```

## Monitoring

### PM2 Monitoring

```bash
# View status
pm2 status

# View logs
pm2 logs linear-frontend

# Monitor resources
pm2 monit

# Restart application
pm2 restart linear-frontend
```

### nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Application Logs

```bash
# PM2 logs
pm2 logs linear-frontend --lines 100

# Application logs
tail -f logs/out.log
tail -f logs/err.log
```

## Health Checks

### WebSocket Health

```bash
# Check WebSocket connection
wscat -c wss://your-domain.com
```

### API Health

```bash
# Check API endpoint
curl https://your-domain.com/api/health
```

## Troubleshooting

### WebSocket Connection Fails

1. Check nginx WebSocket configuration
2. Verify SSL certificate is valid
3. Check firewall allows WebSocket connections
4. Test with `wscat -c wss://your-domain.com`

### Webhook Signature Invalid

1. Verify `LINEAR_WEBHOOK_SECRET` matches Linear webhook secret
2. Check webhook payload is not modified by proxy
3. Test signature verification locally

### Application Crashes

1. Check PM2 logs: `pm2 logs`
2. Check system resources: `pm2 monit`
3. Verify environment variables are set
4. Check for port conflicts

### High Memory Usage

1. Restart application: `pm2 restart linear-frontend`
2. Check for memory leaks in logs
3. Consider increasing server resources
4. Monitor WebSocket connections: check for connection leaks

## Backup and Recovery

### Backup Configuration

```bash
# Backup environment variables
cp .env.local .env.backup

# Backup PM2 configuration
pm2 save

# Backup nginx configuration
sudo cp /etc/nginx/sites-available/linear-frontend /backup/
```

### Recovery

```bash
# Restore from backup
cp .env.backup .env.local

# Restart services
pm2 restart all
sudo systemctl restart nginx
```

## Security Checklist

- [ ] SSL/TLS certificate installed and valid
- [ ] Environment variables secured (not in git)
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] Webhook signature verification enabled
- [ ] Security headers configured in nginx
- [ ] Regular security updates applied
- [ ] Logs monitored for suspicious activity
- [ ] Backup strategy in place

## Performance Optimization

### 1. Enable Caching

```nginx
# In nginx configuration
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

location /_next/static {
    proxy_cache my_cache;
    proxy_cache_valid 200 60m;
}
```

### 2. Enable Compression

```nginx
# In nginx configuration
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
```

### 3. Optimize PM2

```javascript
// In ecosystem.config.js
module.exports = {
  apps: [{
    max_memory_restart: '500M', // Restart if memory exceeds 500MB
    node_args: '--max-old-space-size=512', // Limit Node.js memory
  }]
};
```

## Resources

- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [nginx WebSocket Proxy](https://nginx.org/en/docs/http/websocket.html)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)
