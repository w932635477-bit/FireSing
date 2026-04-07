#!/bin/bash
set -e
echo "Requesting SSL certificate for firesing.cn..."
mkdir -p /opt/FireSing/certbot/www /opt/FireSing/certbot/conf
docker stop firesing-certbot-1 2>/dev/null || true
docker run --rm \
  -v /opt/FireSing/certbot/conf:/etc/letsencrypt \
  -v /opt/FireSing/certbot/www:/var/www/certbot \
  certbot/certbot \
  certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  -d firesing.cn \
  --email 932635477@qq.com \
  --agree-tos \
  --no-eff-email
echo "Restoring nginx config..."
cp /opt/FireSing/nginx.conf.final /opt/FireSing/nginx.conf 2>/dev/null || true
rm -f /opt/FireSing/nginx.conf.final
docker compose -f /opt/FireSing/docker-compose.yml restart nginx
echo "Done! Testing..."
sleep 2
curl -I https://firesing.cn 2>/dev/null || echo "HTTPS not ready yet, DNS may need time"
