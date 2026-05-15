# SSL Certificates

This directory contains SSL/TLS certificates for iamaim.ru.

## Setup

### Option 1: Let's Encrypt with Certbot (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Stop nginx temporarily
docker-compose stop nginx

# Obtain certificate
sudo certbot certonly --standalone \
    -d iamaim.ru \
    -d www.iamaim.ru \
    --email me@mikhaileliseev.com \
    --agree-tos \
    --no-eff-email

# Copy certificates to project
sudo cp /etc/letsencrypt/live/iamaim.ru/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/iamaim.ru/privkey.pem ssl/
sudo chown $USER:$USER ssl/*.pem

# Start nginx
docker-compose start nginx
```

### Option 2: Self-Signed (Development Only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/privkey.pem \
    -out ssl/fullchain.pem \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=AIM/CN=iamaim.ru"
```

## Auto-Renewal

Add to crontab for automatic renewal:

```bash
sudo crontab -e

# Add this line:
0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/iamaim.ru/*.pem /path/to/project/ssl/ && docker-compose restart nginx
```

## Files

- `fullchain.pem` - Full certificate chain
- `privkey.pem` - Private key

**Note:** These files are in .gitignore and should never be committed.
