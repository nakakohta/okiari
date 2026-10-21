# okiari

飲食業務の報告、在庫管理、共同編集を行うアプリです。画面は Vue 3 / Vite、API と WebSocket は FastAPI、認証・データ・リアルタイム通知は Supabase を使用します。

## 設定

Docker Compose では `.env.example` をルートの `.env` にコピーして設定します。直接起動する場合は、Vite 用の `VITE_*` 変数を `frontend/.env`、FastAPI 用の `SUPABASE_*` 変数を `backend/.env` に設定します。`backend/.env.example` も参照してください。

| 変数 | 用途 |
| --- | --- |
| `VITE_SUPABASE_URL` | ブラウザから接続する Supabase プロジェクト URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | ブラウザ公開用の publishable key |
| `SUPABASE_URL` | FastAPI から接続する Supabase プロジェクト URL |
| `SUPABASE_SERVICE_ROLE_KEY` | FastAPI 専用の秘密鍵。ブラウザには公開しない |
| `VITE_API_BASE_URL` | 開発時に API が別のホストにある場合の URL。省略時は同じホストの 18000 番ポートを使用 |
| `CORS_ORIGINS` | 開発時に許可する画面の URL。カンマ区切り |

Supabase には `supabase/migrations` のマイグレーションを適用してください。`.env` は Git に含めないでください。

## ローカル開発

Node.js 22、npm、Python 3.13、uv が必要です。上記のとおり `frontend/.env` と `backend/.env` を用意します。

```sh
npm ci
npm --workspace frontend run dev
```

別のターミナルで:

```sh
cd backend
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 18000
```

画面は `http://localhost:5173`、API ヘルスチェックは `http://127.0.0.1:18000/health` です。LAN 内で共同編集を試す場合は `npm --workspace frontend run dev:shared` と、FastAPI の `--host 0.0.0.0` を使います。

Docker Compose で開発する場合は、ルートの `.env` を用意して次を実行します。

```sh
docker compose up --build
```

画面は `http://localhost:5173`、API ヘルスチェックは `http://localhost:18000/health` です。Compose のフロントエンドはルート `.env` の公開用 `VITE_*` 変数だけを受け取り、バックエンドは Supabase のサーバ用変数を受け取ります。

## Docker Compose による配信

Docker Compose の本番用設定は、通常の Vite 静的ビルドを Nginx で配信し、API と WebSocket を FastAPI に転送します。Supabase は引き続き外部サービスとして必要です。ルートの `.env` に上記の値を設定し、次を実行します。

```sh
docker compose --env-file .env -f docker-compose.prod.yml up --build -d
```

画面は `http://localhost:8080`、ヘルスチェックは `http://localhost:8080/health` です。公開時は HTTPS 対応のリバースプロキシを前段に置き、必要なら `APP_PORT` で公開ポートを変更してください。フロントエンドの Supabase URL と publishable key はビルド時に埋め込まれるため、変更後は再ビルドします。`SUPABASE_SERVICE_ROLE_KEY` はバックエンドの実行環境だけに渡されます。

Nginx 以外の静的ホスティングを使う場合は `npm run build` で生成される `frontend/dist` を配信します。Vue Router の画面パスを `index.html` にフォールバックさせ、API と `/ws/` を FastAPI に転送してください。API が別のオリジンにある場合は、ビルド時に `VITE_API_BASE_URL` を FastAPI の公開 URL に設定します。

## 検証

```sh
npm run build
npm run test:realtime
cd backend && uv run python -m unittest discover -s tests
```
