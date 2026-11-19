#!/usr/bin/env bash
# OkiAri - Ubuntu Server / VirtualBox deployment
# Prerequisites: source files in /opt/okiari and populated /opt/okiari/.env
set -Eeuo pipefail

APP_DIR=/opt/okiari
COMPOSE_FILE=docker-compose.vm.yml

if (( EUID != 0 )); then
  echo 'エラー: sudo bash setup-okiari-vm.sh で実行してください。' >&2
  exit 1
fi

# Fail before changing the host when required application settings are missing.
python3 - "$APP_DIR" "$COMPOSE_FILE" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
filename = sys.argv[2]
source = root / "docker-compose.prod.yml"
env_file = root / ".env"
if not (root / "frontend" / "Dockerfile.prod").is_file() or not source.is_file():
    sys.exit("エラー: /opt/okiari に本番用ソースコードが見つかりません。")
if not env_file.is_file():
    sys.exit("エラー: /opt/okiari/.env がありません。事前にSupabase情報を設定してください。")

env = {}
for line in env_file.read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    env[key.strip()] = value.strip().strip('"\'')

required = (
    "VITE_SUPABASE_URL", "VITE_SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"
)
missing = [key for key in required if not env.get(key) or "YOUR_" in env[key]]
if missing:
    sys.exit("エラー: .env の次の項目を設定してください: " + ", ".join(missing))
if env.get("VITE_API_BASE_URL", ""):
    sys.exit("エラー: 同一オリジン配信のため .env の VITE_API_BASE_URL= は空欄にしてください。")

original = source.read_text(encoding="utf-8")
patterns = (
    '"${APP_PORT:-8080}:80"',
    '"127.0.0.1:${APP_PORT:-8080}:80"',
)
if not any(p in original for p in patterns):
    sys.exit("エラー: Composeのポート設定が想定と異なります。自動変更は中止しました。")
for p in patterns:
    original = original.replace(p, '"127.0.0.1:8080:80"')
(root / filename).write_text(original, encoding="utf-8")
PY

chmod 600 "$APP_DIR/.env"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx ca-certificates curl

# Install Docker Engine only on VMs where Docker is not present.
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

systemctl enable --now docker

# Launch the existing production application, but on loopback port 8080 only.
cd "$APP_DIR"
docker compose -p okiari-vm --env-file .env -f "$COMPOSE_FILE" up --build -d

# Configure the host Nginx as the HTTP reverse proxy.
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
if [[ -f /etc/nginx/sites-available/okiari ]]; then
  cp -a /etc/nginx/sites-available/okiari "/etc/nginx/sites-available/okiari.bak.$(date +%Y%m%d%H%M%S)"
fi
cat > /etc/nginx/sites-available/okiari <<'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
NGINX
ln -sfn /etc/nginx/sites-available/okiari /etc/nginx/sites-enabled/okiari
rm -f /etc/nginx/sites-enabled/default
systemctl enable nginx
systemctl restart nginx

# Open HTTP only when UFW is installed; do not enable UFW automatically.
if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp
fi

printf '\n構築処理が終了しました。Windowsから http://<UbuntuのIPアドレス>/ にアクセスしてください。\n'
printf 'VirtualBoxがNAT接続の場合は、ホストポート8080→ゲストポート80の転送設定が必要です。\n'
