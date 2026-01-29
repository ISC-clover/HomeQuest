# ビルドステージ
FROM node:18-alpine as build

WORKDIR /app

# package.json をコピー
COPY package.json ./

# 依存関係をインストール
RUN npm install

# ソースコードをコピー
COPY . .

# 本番用ビルド
RUN npm run build

# 本番ステージ
FROM node:18-alpine

WORKDIR /app

# serve をグローバルインストール（静的ファイル配信用）
RUN npm install -g serve

# ビルドステージから dist をコピー
COPY --from=build /app/dist ./dist

# ポート 3000 を公開
EXPOSE 3000

# アプリケーション起動
CMD ["serve", "-s", "dist", "-l", "3000"]
