# okiari

本プロジェクトでは、フロントエンドに Vue.js + TypeScript、バックエンドに FastAPI + Python を使用します。

DBはSupaBaseを使用します
## 概要

このアプリケーションでは、飲食業務に関する報告・確認・管理を効率化することを目的としています。

主な対象業務は以下のとおりです。

* 食数報告
* ドリンク補充
* フード・ドリンク関連データの管理
* 在庫・棚卸関連データの管理
* ユーザー権限に応じた業務データの確認・編集

## 技術スタック

### フロントエンド

* Vue.js
* TypeScript
* Vue Router
* Pinia
* ESLint
* Prettier
* Vite

### バックエンド

* Python
* FastAPI
* uv

### 今後追加予定

* データベース
* 認証機能
* ユーザー権限管理
* Docker
* 本番環境へのデプロイ

## ディレクトリ構成

```text
okiari/
├─ package.json
├─ package-lock.json
├─ src/
├─ public/
├─ vite.config.ts
├─ tsconfig.json
└─ backend/
   ├─ pyproject.toml
   ├─ uv.lock
   └─ app/
      ├─ __init__.py
      └─ main.py
```

## 環境

### フロントエンド

* Node.js
* npm

### バックエンド

* Python
* uv

## チーム開発時の環境構築手順

この手順は、GitHubなどからリポジトリを `git clone` した後に、各メンバーのPCで開発環境を構築するための手順です。

### 1. 前提条件

事前に以下がインストールされていることを確認します。

* Git
* Node.js
* npm
* Python
* uv

バージョン確認は以下のコマンドで行います。

```bash
git --version
node -v
npm -v
python --version
uv --version
```

`uv` がインストールされていない場合は、PowerShellで以下を実行します。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

インストール後、ターミナルを開き直して以下を確認します。

```bash
uv --version
```

### 2. リポジトリをクローンする

作業用フォルダへ移動します。

```bash
cd /c/Users/nakak/workspase
```

リポジトリをクローンします。

```bash
git clone <repository-url> okiari
```

作成されたプロジェクトフォルダへ移動します。

```bash
cd okiari
```

### 3. フロントエンドの依存パッケージをインストールする

プロジェクトルートで以下を実行します。

```bash
npm install
```

これにより、`package.json` と `package-lock.json` をもとに必要なパッケージがインストールされます。

### 4. バックエンドの依存パッケージをインストールする

`backend` ディレクトリへ移動します。

```bash
cd backend
```

uvで依存パッケージを同期します。

```bash
uv sync
```

これにより、`pyproject.toml` と `uv.lock` をもとにFastAPIなどのバックエンド用パッケージがインストールされます。

完了したら、プロジェクトルートへ戻ります。

```bash
cd ..
```

### 5. 開発サーバーを起動する

開発時は、ターミナルを2つ開いて、フロントエンドとバックエンドを別々に起動します。

#### ターミナル1：フロントエンド

```bash
cd /c/Users/nakak/workspase/okiari
npm run dev
```

起動後、以下のURLにアクセスします。

```text
http://localhost:5173
```

#### ターミナル2：バックエンド

```bash
cd /c/Users/nakak/workspase/okiari/backend
uv run fastapi dev app/main.py --host 127.0.0.1 --port 18000
```

起動後、以下のURLにアクセスします。

```text
http://127.0.0.1:18000
```

APIドキュメントは以下のURLで確認できます。

```text
http://127.0.0.1:18000/docs
```

### 6. 動作確認

フロントエンドとバックエンドが起動できたら、以下を確認します。

| 種別        | URL                         | 確認内容             |
| --------- | --------------------------- | ---------------- |
| フロントエンド   | <http://localhost:5173>       | Vueの画面が表示される     |
| バックエンド    | <http://127.0.0.1:18000>      | FastAPIのレスポンスが返る |
| APIドキュメント | <http://127.0.0.1:18000/docs> | Swagger UIが表示される |

### 7. 最新の変更を取り込む場合

他のメンバーが変更した内容を取り込む場合は、プロジェクトルートで以下を実行します。

```bash
git pull
```

フロントエンドの依存パッケージが変更されている可能性がある場合は、以下を実行します。

```bash
npm install
```

バックエンドの依存パッケージが変更されている可能性がある場合は、以下を実行します。

```bash
cd backend
uv sync
cd ..
```

### 8. 注意事項

`node_modules` や `.venv` はGit管理しません。

各メンバーのPCで以下のコマンドを実行して、それぞれの環境に必要なパッケージをインストールします。

```bash
npm install
```

```bash
cd backend
uv sync
```

FastAPIは通常 `8000` 番ポートで起動しますが、本環境では `WinError 10013` が発生したため、`18000` 番ポートを使用しています。

そのため、バックエンドのURLは以下を使用します。

```text
http://127.0.0.1:18000
```

## セットアップ手順

## フロントエンドの起動方法

### 1. 依存パッケージのインストール

```bash
npm install
```

### 2. 開発サーバーの起動

```bash
npm run dev
```

起動後、以下の URL にアクセスします。

```text
http://localhost:5173
```

## バックエンドの起動方法

### 1. backend ディレクトリへ移動

```bash
cd /c/Users/nakak/workspase/okiari/backend
```

### 2. FastAPI 開発サーバーの起動

本環境では、8000 番ポートや 8080 番ポートで起動できない場合があったため、18000 番ポートを使用します。

```bash
uv run fastapi dev app/main.py --host 127.0.0.1 --port 18000
```

起動後、以下の URL にアクセスします。

```text
http://127.0.0.1:18000
```

API ドキュメントは以下の URL で確認できます。

```text
http://127.0.0.1:18000/docs
```

## 開発時の起動方法

開発時は、ターミナルを2つ開いて、フロントエンドとバックエンドを同時に起動します。

### ターミナル1：フロントエンド

```bash
cd /c/Users/nakak/workspase/okiari
npm run dev
```

### ターミナル2：バックエンド

```bash
cd /c/Users/nakak/workspase/okiari/backend
uv run fastapi dev app/main.py --host 127.0.0.1 --port 18000
```

## アクセスURL

| 種別        | URL                         |
| --------- | --------------------------- |
| フロントエンド   | <http://localhost:5173>       |
| バックエンド    | <http://127.0.0.1:18000>      |
| APIドキュメント | <http://127.0.0.1:18000/docs> |

## バックエンドの動作確認

`backend/app/main.py` に以下のようなエンドポイントを作成しています。

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

以下の URL にアクセスしてレスポンスが返れば、FastAPI は正常に起動しています。

```text
http://127.0.0.1:18000/
```

期待されるレスポンス：

```json
{
  "message": "FastAPI is running"
}
```

ヘルスチェック用 URL：

```text
http://127.0.0.1:18000/health
```

期待されるレスポンス：

```json
{
  "status": "ok"
}
```

## 注意事項

### ポート番号について

FastAPI は通常 `8000` 番ポートで起動しますが、本環境では `WinError 10013` が発生したため、`18000` 番ポートを使用しています。

そのため、バックエンドのURLは以下を使用します。

```text
http://127.0.0.1:18000
```

### フロントエンドとバックエンドの違い

| 項目      | 使用技術    | 起動コマンド                                                         | ポート   |
| ------- | ------- | -------------------------------------------------------------- | ----- |
| フロントエンド | Vue.js  | `npm run dev`                                                  | 5173  |
| バックエンド  | FastAPI | `uv run fastapi dev app/main.py --host 127.0.0.1 --port 18000` | 18000 |

## 今後の開発予定

* 画面設計
* API設計
* データベース設計
* 認証機能の実装
* ユーザー権限管理の実装
* フロントエンドとバックエンドの接続
* Docker環境の構築
* 本番環境へのデプロイ

## 開発メモ

現在は、フロントエンドとバックエンドの基本的な開発環境を構築した段階です。

今後は、業務で使用するデータ構造を整理し、APIと画面を少しずつ実装していきます。

# okiari

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

* Chromium-based browsers (Chrome, Edge, Brave, etc.):
  * [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  * [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
* Firefox:
  * [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  * [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
