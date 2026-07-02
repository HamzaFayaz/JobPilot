#!/usr/bin/env bash
# One-time HTTPS setup on EC2 — free Let's Encrypt cert for Gmail OAuth.
# Prerequisites: instance running, port 443 open, DOMAIN DNS → Elastic IP.
#
# Usage (on EC2):
#   export DOMAIN=jobpilot-hamza.duckdns.org
#   export CERTBOT_EMAIL=your-email@example.com
#   bash deploy/setup-https.sh
set -euo pipefail

APP_DIR=/opt/jobpilot
DOMAIN="${DOMAIN:-43.98.197.132}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

if [ -z "$CERTBOT_EMAIL" ]; then
  echo "ERROR: Set CERTBOT_EMAIL (Let's Encrypt requires an email)."
  echo "  export CERTBOT_EMAIL=you@example.com"
  exit 1
fi

cd "$APP_DIR"

echo "==> Installing certbot..."
sudo apt-get update
sudo apt-get install -y certbot gettext-base

echo "==> Stopping web container (free port 80 for standalone challenge)..."
sudo docker compose stop web || true

echo "==> Requesting certificate for ${DOMAIN}..."
sudo certbot certonly --standalone \
  -d "$DOMAIN" \
  --non-interactive \
  --agree-tos \
  -m "$CERTBOT_EMAIL"

echo "==> Enabling HTTPS nginx config..."
export DOMAIN
envsubst '${DOMAIN}' < deploy/nginx-docker-ssl.conf.template > deploy/nginx-active.conf

echo "==> Restarting stack..."
bash deploy/remote-update.sh

echo ""
echo "HTTPS ready: https://${DOMAIN}"
echo "Next: update GitHub Secrets FRONTEND_URL and redeploy (or set in .env):"
echo "  FRONTEND_URL=https://${DOMAIN}"
echo "  GOOGLE_REDIRECT_URI=https://${DOMAIN}/auth/google/callback"
