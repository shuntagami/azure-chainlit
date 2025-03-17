import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# モデルのインポート
from app.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 環境変数からDB接続情報を取得
section = config.config_ini_section
config.set_section_option(section, "APP_DATABASE_HOST", os.getenv("APP_DATABASE_HOST", "db"))
config.set_section_option(section, "APP_DATABASE_USERNAME", os.getenv("APP_DATABASE_USERNAME", "postgres"))
config.set_section_option(section, "APP_DATABASE_PASSWORD", os.getenv("APP_DATABASE_PASSWORD", "postgres"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# ... existing code ...
