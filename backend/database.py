from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_database():
    """Create all tables and seed the account if it doesn't exist."""
    from models.account import Account
    from models.position import Position  # noqa: F401
    from models.order import Order  # noqa: F401
    from models.trade import Trade  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed account row if not exists
    async with async_session() as session:
        from sqlalchemy import select
        from config import INITIAL_BALANCE

        result = await session.execute(select(Account).where(Account.id == 1))
        account = result.scalar_one_or_none()
        if account is None:
            account = Account(
                id=1,
                initial_balance=INITIAL_BALANCE,
                cash_balance=INITIAL_BALANCE,
            )
            session.add(account)
            await session.commit()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
