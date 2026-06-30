#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 22.04 EC2 instance.
# Run on the server: bash bootstrap-ec2.sh
set -euo pipefail

APP_DIR=/opt/jobpilot

echo "==> Installing Docker..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl git rsync gettext-base
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME:-$VERSION}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu

echo "==> Preparing application directory..."
sudo mkdir -p "$APP_DIR/data/uploads"
sudo chown -R ubuntu:ubuntu "$APP_DIR"

if [ ! -f "$APP_DIR/.env" ]; then
  echo ""
  echo "NEXT: Create production .env on the server:"
  echo "  nano $APP_DIR/.env"
  echo "  (copy from .env.example — set FRONTEND_URL, OAuth redirect URIs, API keys)"
  echo ""
fi

echo "==> Generating deploy SSH key for GitHub Actions (if missing)..."
DEPLOY_KEY="$HOME/.ssh/jobpilot_github_actions"
if [ ! -f "$DEPLOY_KEY" ]; then
  ssh-keygen -t ed25519 -f "$DEPLOY_KEY" -N "" -C "jobpilot-github-actions"
  cat "$DEPLOY_KEY.pub" >> "$HOME/.ssh/authorized_keys"
  chmod 600 "$HOME/.ssh/authorized_keys"
  echo ""
  echo "Add this PRIVATE key to GitHub → Settings → Secrets → EC2_SSH_KEY:"
  echo "-------------------------------------------------------------------"
  cat "$DEPLOY_KEY"
  echo "-------------------------------------------------------------------"
else
  echo "Deploy key already exists at $DEPLOY_KEY"
fi

echo ""
echo "Bootstrap complete."
echo ""
echo "IMPORTANT: Log out and SSH back in so the docker group applies."
echo ""
echo "GitHub repository secrets (Settings → Secrets and variables → Actions):"
echo "  EC2_HOST    = your Elastic IP or public DNS"
echo "  EC2_USER    = ubuntu"
echo "  EC2_SSH_KEY = private key printed above"
echo ""
echo "After .env exists on the server, push to main — GitHub Actions deploys via Docker Compose."
