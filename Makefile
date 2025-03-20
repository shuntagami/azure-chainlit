.PHONY: migrate-create migrate-up migrate-down migrate-current migrate-history migrate-reset migrate-help seed seed-help

# マイグレーション関連コマンド
migrate-create:
	@read -p "マイグレーション名を入力: " name; \
	docker compose run --rm chainlit-app alembic revision --autogenerate -m "$$name"

migrate-up:
	docker compose run --rm chainlit-app alembic upgrade head

migrate-down:
	docker compose run --rm chainlit-app alembic downgrade -1

migrate-current:
	docker compose run --rm chainlit-app alembic current

migrate-history:
	docker compose run --rm chainlit-app alembic history

migrate-reset:
	docker compose down -v
	rm -f app/migrations/versions/*.py
	docker compose up -d db
	docker compose run --rm chainlit-app alembic revision --autogenerate -m "initial"
	docker compose run --rm chainlit-app alembic upgrade head

migrate-help:
	@echo "マイグレーションコマンド:"
	@echo "  make migrate-create  - 新しいマイグレーションを作成"
	@echo "  make migrate-up      - 最新バージョンにマイグレーション"
	@echo "  make migrate-down    - 1つ前のバージョンに戻す"
	@echo "  make migrate-current - 現在のマイグレーションバージョンを表示"
	@echo "  make migrate-history - マイグレーション履歴を表示"
	@echo "  make migrate-reset   - データベースを削除して再作成し、マイグレーションを適用"

# シード関連コマンド
seed:
	docker compose run --rm chainlit-app python /app/seeds.py

seed-custom:
	@read -p "メールアドレスを入力: " email; \
	read -p "パスワードを入力: " password; \
	docker compose run --rm chainlit-app python /app/seeds.py --email="$$email" --password="$$password"

seed-help:
	@echo "シードコマンド:"
	@echo "  make seed          - デフォルトユーザー(shuntagami23@gmail.com, password123)を登録"
	@echo "  make seed-custom   - カスタムユーザーを登録"
