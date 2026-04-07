#!/bin/bash
set -e

DOMAIN="firesing.cn"
EMAIL="${1:-admin@firesing.cn}"

echo "=== Step 1: Start nginx in HTTP-only mode ==="
# Temporarily use a simple HTTP config for cert generation
cat > /tmp/nginx-certonly.conf << 'EOF'
events {
    worker_connections 1024;
}
http {
    server {
        listen 80;
        server_name firesing.cn;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
    }
}
EOF

# Backup original and swap
cp /opt/FireSing/nginx.conf /opt/FireSing/nginx.conf.final
cp /tmp/nginx-certonly.conf /opt/FireSing/nginx.conf
docker compose -f /opt/FireSing/docker-compose.yml restart nginx

echo "=== Step 2: Request certificate ==="
mkdir -p /opt/FireSing/certbot/www /opt/FireSing/certbot/conf
docker compose -f /opt/FireSing/docker-compose.yml run --rm certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email

echo "=== Step 3: Restore full nginx config ==="
cp /opt/FireSing/nginx.conf.final /opt/FireSing/nginx.conf
rm /opt/FireSing/nginx.conf.final
docker compose -f /opt/FireSing/docker-compose.yml restart nginx

echo "=== Done! ==="
echo "Certificate installed for $DOMAIN"
echo "Check: curl -I https://firesing.cn"
