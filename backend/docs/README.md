# HomeQuest API 仕様書

家事クエストアプリ（HomeQuest）のバックエンドAPIドキュメントです。
Dockerコンテナ上で動作することを前提としています。

## API Base URL

`https://api-clover-homequest.syk9.link`

`docker-compose.yml`にAPIキーを`.env`から読み込むように書き、叩くときはヘッダーに`X-App-Key`という名前でAPIキーを付けること

## 機能詳細

`openapi.json`を参照