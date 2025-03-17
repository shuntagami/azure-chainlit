.PHONY: migrate-create migrate-up migrate-down migrate-current migrate-history migrate-help

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

migrate-help:
	@echo "マイグレーションコマンド:"
	@echo "  make migrate-create  - 新しいマイグレーションを作成"
	@echo "  make migrate-up      - 最新バージョンにマイグレーション"
	@echo "  make migrate-down    - 1つ前のバージョンに戻す"
	@echo "  make migrate-current - 現在のマイグレーションバージョンを表示"
	@echo "  make migrate-history - マイグレーション履歴を表示"
