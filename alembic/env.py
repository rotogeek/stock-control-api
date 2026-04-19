"""
alembic/env.py - Alembic migration environment
================================================

WHY THIS FILE EXISTS:
Alembic needs three things to generate and run migrations:
  1. The database URL to connect to.
  2. The metadata (Base.metadata) so it knows what the schema should look like.
  3. All ORM models imported so they are registered on Base.metadata before
     autogenerate inspects it. If a model isn't imported here, Alembic won't
     see its table and will generate a DROP TABLE for it.

TWO RUN MODES:
  offline — generates SQL scripts without a live DB connection (useful for
            review / production deployment pipelines).
  online  — connects to the DB and applies migrations directly (dev workflow).
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Pull DATABASE_URL from our app config (reads .env via python-dotenv)
# ---------------------------------------------------------------------------
from app import Config as app_config  # noqa: E402

# ---------------------------------------------------------------------------
# Import Base so Alembic knows about the metadata.
# Import ALL ORM models so their tables are registered on Base.metadata.
# Without these imports, autogenerate won't detect the tables.
# ---------------------------------------------------------------------------
from app.database import Base  # noqa: E402
import app.models.orm  # noqa: F401, E402  — registers all 6 ORM models

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Inject our DATABASE_URL so Alembic uses the same connection as the app.
# This overrides the (commented-out) sqlalchemy.url in alembic.ini.
config.set_main_option("sqlalchemy.url", app_config.DATABASE_URL)

# Set up Python logging from the alembic.ini [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata autogenerate compares against.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode — emit SQL to stdout, no live connection needed
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without a database connection.

    Useful for generating a .sql file to review before applying,
    or for deployment pipelines that don't have direct DB access.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — connect and apply migrations directly
# ---------------------------------------------------------------------------

def run_migrations_online() -> None:
    """
    Run migrations against a live database connection.

    NullPool is used here to avoid connection pool overhead during migration
    runs, which are short-lived processes — not long-running servers.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
