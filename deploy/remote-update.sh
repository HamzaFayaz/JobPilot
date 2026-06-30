#!/usr/bin/env bash
# Runs on EC2 after each deploy — rebuild and restart Docker containers.
set -euo pipefail

APP_DIR=/opt/jobpilot
cd "$APP_DIR"

if [ ! -f .env ]; then
  echo "ERROR: $APP_DIR/.env not found. Copy .env.example and set production values."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker not installed. Run deploy/bootstrap-ec2.sh first."
  exit 1
fi

# shellcheck disable=SC1091
set -a && source .env && set +a
DOMAIN="${DOMAIN:-jobpilot-hamza.duckdns.org}"

if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  export DOMAIN
  envsubst '${DOMAIN}' < deploy/nginx-docker-ssl.conf.template > deploy/nginx-active.conf
  echo "Using HTTPS nginx config for ${DOMAIN}"
else
  cp deploy/nginx-docker.conf deploy/nginx-active.conf
  echo "Using HTTP nginx config (run deploy/setup-https.sh for Gmail OAuth)"
fi

sudo docker compose build
sudo docker compose up -d --remove-orphans
sudo docker compose ps

if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  curl -sf "https://${DOMAIN}/health" >/dev/null
else
  curl -sf http://127.0.0.1/health >/dev/null
fi
echo "Deploy complete — JobPilot containers healthy."
