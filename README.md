# Azure Chainlit

## データベースマイグレーション

### 初期セットアップ
```bash
# 依存関係インストール
pip install alembic

# 環境変数設定
export APP_DATABASE_HOST=localhost
export APP_DATABASE_USERNAME=postgres
export APP_DATABASE_PASSWORD=postgres
```

### マイグレーション操作（ローカル環境）
```bash
# 新しいマイグレーション作成（モデル変更後）
alembic revision --autogenerate -m "変更内容の説明"

# マイグレーション実行
alembic upgrade head

# 現在のマイグレーション状態確認
alembic current
```

### マイグレーション操作（Docker環境）
Docker Compose環境では、Makefileに定義されたコマンドを使用できます：

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

### モデル変更の流れ
1. `app/database.py`でモデルを変更
2. マイグレーション作成コマンドで変更を検出
3. 生成されたマイグレーションスクリプトを確認（migrations/versions/内）
4. マイグレーション実行コマンドで変更を適用
