name: Deploy inference-service (latest)

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy to EC2 via SSH (pull latest + restart + ready check)
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}          # Elastic IP or DNS
          username: ${{ secrets.EC2_USER }}      # usually ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}        # private key
          script: |
            set -euo pipefail

            cd ~/my-mlops-demo

            echo "== Pull latest =="
            docker compose pull inference-service

            echo "== Restart service =="
            docker compose up -d --no-deps inference-service

            echo "== Show running containers =="
            docker compose ps

            echo "== Wait for /ready (timeout 180s) =="
            start=$(date +%s)
            until curl -fsS http://127.0.0.1:8000/ready >/dev/null 2>&1; do
              now=$(date +%s)
              elapsed=$((now - start))
              if [ "$elapsed" -ge 180 ]; then
                echo "!! TIMEOUT waiting for /ready"
                docker compose logs --tail=200 inference-service || true
                exit 1
              fi
              sleep 3
            done

            echo "✅ /ready OK"

            echo "== Image digest running =="
            CID=$(docker compose ps -q inference-service)
            docker inspect --format='{{.Name}}  {{.Config.Image}}  {{index .RepoDigests 0}}' "$CID" || true
