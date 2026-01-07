#!/usr/bin/env bash
set -euo pipefail

# --- config ---
SERVICE_NAME="inference-service"     # docker compose service name
READY_URL="http://127.0.0.1:8000/ready"
HEALTH_URL="http://127.0.0.1:8000/health"
TIMEOUT_SECS=180

echo "== Pull latest =="
docker compose pull "${SERVICE_NAME}"

echo "== Restart service =="
docker compose up -d --no-deps "${SERVICE_NAME}"

echo "== Show running containers =="
docker compose ps

echo "== Quick health check =="
curl -fsS "${HEALTH_URL}" || true
echo

echo "== Wait for ready (timeout ${TIMEOUT_SECS}s) =="
start=$(date +%s)
until curl -fsS "${READY_URL}" >/dev/null 2>&1; do
  now=$(date +%s)
  elapsed=$((now - start))
  if [ "${elapsed}" -ge "${TIMEOUT_SECS}" ]; then
    echo "!! TIMEOUT waiting for /ready"
    echo "== Last logs =="
    docker compose logs --tail=200 "${SERVICE_NAME}" || true
    exit 1
  fi
  sleep 3
done

echo "✅ /ready is OK"

echo "== Image + digest running =="
CID=$(docker compose ps -q "${SERVICE_NAME}")
docker inspect --format='{{.Name}}  {{.Config.Image}}  {{index .RepoDigests 0}}' "${CID}" || true
