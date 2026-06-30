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

docker compose build
docker compose up -d --remove-orphans
docker compose ps

curl -sf http://127.0.0.1/health >/dev/null
echo "Deploy complete — JobPilot containers healthy."
