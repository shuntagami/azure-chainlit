# Azure Chainlit

# マイグレーション操作

```bash
# 新しいマイグレーション作成
make migrate-create

# マイグレーション実行
make migrate-up

# 1つ前のバージョンに戻す
make migrate-down

# 現在のマイグレーション状態確認
make migrate-current

# マイグレーション履歴表示
make migrate-history

# ヘルプ表示
make migrate-help
```

## モデル変更の流れ

1. `app/models.py`でモデルを変更
2. マイグレーション作成コマンドで変更を検出
3. 生成されたマイグレーションスクリプトを確認（migrations/versions/内）
4. マイグレーション実行コマンドで変更を適用

# SSH 接続のための App Service 設定と DB マイグレーション手順の追加

## 変更内容

- Azure App Service で SSH 接続を有効にするための設定を追加
- データベースマイグレーションを SSH 経由で実行するための手順を追加

## 技術的詳細

- SSH の設定は Microsoft のドキュメントに基づいています
- ルートパスワードは「Docker!」に設定されています（Azure App Service の要件）
- SSH はポート 2222 を使用します（Azure App Service の要件）
- データベースマイグレーションコマンドは Alembic CLI を直接使用します
- Terraform の設定に`WEBSITES_SSH_ENABLED`アプリ設定を追加
- `APP_DATABASE_NAME`環境変数を追加してデータベース接続を確保

## テスト

- Docker イメージのビルドとローカル実行で SSH 接続をテスト済み

Link to Devin run: https://app.devin.ai/sessions/f6ead96128d14e41bc40331130bb3abe
Requested by: shuntagami
