# Azure Chainlit

## マイグレーション操作

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
1. `app/models.py`でモデルを変更
2. マイグレーション作成コマンドで変更を検出
3. 生成されたマイグレーションスクリプトを確認（migrations/versions/内）
4. マイグレーション実行コマンドで変更を適用
