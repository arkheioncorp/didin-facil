import asyncio
from logging.config import fileConfig

from alembic import context
# Import your models and settings
from api.database.models import Base
from shared.config import settings
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url from settings
# Handle different URL formats from Railway, Docker, etc.
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)

# For sync migrations, use psycopg2 (default driver)
sync_db_url = db_url
if "+asyncpg" in sync_db_url:
    sync_db_url = sync_db_url.replace("+asyncpg", "")

print(f"[Alembic] Using database URL: {db_url[:50]}...")
config.set_main_option("sqlalchemy.url", sync_db_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_sync() -> None:
    """Run migrations in synchronous mode using psycopg2."""
    from sqlalchemy import create_engine
    
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()
    
    connectable.dispose()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async).

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # For async, need to use asyncpg driver
    async_url = config.get_main_option("sqlalchemy.url")
    if not "+asyncpg" in async_url:
        async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
    
    config.set_main_option("sqlalchemy.url", async_url)
    
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Use sync migrations to avoid asyncio.run() issues
    run_migrations_sync()
# Force deploy qui 04 dez 2025 16:05:24 -04
