#!/bin/bash
# ========================================
# FireSing 一键部署脚本
# 适用于: 腾讯云 HK 轻量服务器 (Ubuntu 22.04)
# ========================================
set -e

echo "🔥 FireSing 部署开始"
echo "===================="

# --- 0. 检查环境 ---
command -v docker >/dev/null 2>&1 || { echo "安装 Docker..."; curl -fsSL https://get.docker.com | sh; }
command -v docker compose >/dev/null 2>&1 || { echo "安装 Docker Compose..."; apt-get update && apt-get install -y docker-compose-plugin; }

# --- 1. 配置 ---
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从模板创建..."
    cp .env.example .env
    echo "请编辑 .env 填写实际配置后再运行"
    echo "  nano .env"
    exit 1
fi

source .env

# --- 2. 创建数据目录 ---
mkdir -p data/songs data/segments data/converted data/outputs data/voices data/models
echo "✅ 数据目录已创建"

# --- 3. HTTPS 证书 ---
DOMAIN=${DOMAIN:-firesing.cn}
CERT_DIR="./certbot/conf/live/$DOMAIN"

if [ ! -d "$CERT_DIR" ]; then
    echo "📜 申请 Let's Encrypt 证书 ($DOMAIN)..."

    # 先用 HTTP-only nginx 获取证书
    cat > /tmp/nginx-cert.conf << 'NGINX_CONF'
events { worker_connections 1024; }
http {
    server {
        listen 80;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
    }
}
NGINX_CONF

    mkdir -p certbot/www certbot/conf
    docker run --rm -v "$PWD/certbot/www:/var/www/certbot" \
        -v "$PWD/certbot/conf:/etc/letsencrypt" \
        certbot/certbot certonly \
        --webroot --webroot-path /var/www/certbot \
        -d "$DOMAIN" --email "admin@$DOMAIN" \
        --agree-tos --no-eff-email

    rm -f /tmp/nginx-cert.conf
    echo "✅ 证书已获取"
else
    echo "✅ 证书已存在"
fi

# --- 4. 更新 nginx.conf 中的域名 ---
sed -i "s/YOUR_DOMAIN/$DOMAIN/g" nginx.conf
sed -i "s/server_name _;/server_name $DOMAIN;/g" nginx.conf

# --- 5. 构建并启动 ---
echo "🔨 构建 Docker 镜像..."
docker compose build

echo "🚀 启动服务..."
docker compose up -d

# --- 6. 等待启动 ---
echo "⏳ 等待服务就绪..."
sleep 10

# --- 7. 验证 ---
if curl -sf "https://$DOMAIN" > /dev/null 2>&1; then
    echo ""
    echo "🎉 部署成功!"
    echo "   前端: https://$DOMAIN"
    echo "   后端: https://$DOMAIN/api/health"
    echo ""
    echo "下一步:"
    echo "  1. 访问 https://$DOMAIN 验证前端"
    echo "  2. 访问 https://$DOMAIN/api/health 验证后端"
    echo "  3. 上传一首歌测试完整流程"
else
    echo "⚠️  服务可能还在启动，请等待 30 秒后访问 https://$DOMAIN"
    echo "   查看日志: docker compose logs -f"
fi
