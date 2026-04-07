#!/bin/bash
set -e

DOMAIN=firesing.cn
echo "Requesting SSL certificate for $DOMAIN..."

cd /opt/FireSing

# 1. Stop nginx so port 80 is free for certbot standalone
docker compose stop nginx 2>/dev/null || true

# 2. Clean stale certbot state (fixes "No such authorization")
rm -rf certbot/conf/live certbot/conf/renewal certbot/conf/archive 2>/dev/null || true
mkdir -p certbot/conf certbot/www

# 3. Get cert using standalone mode (certbot runs its own temp web server)
docker run --rm \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  -v "$PWD/certbot/www:/var/www/certbot" \
  -p 80:80 \
  certbot/certbot \
  certonly \
  --standalone \
  -d "$DOMAIN" \
  --email 932635477@qq.com \
  --agree-tos \
  --no-eff-email

echo "✅ Certificate obtained!"

# 4. Start everything
docker compose up -d

echo "⏳ Waiting for services..."
sleep 5
curl -I "https://$DOMAIN" 2>/dev/null && echo "✅ HTTPS is working!" || echo "⚠️  HTTPS not ready yet, check: docker compose logs nginx"
