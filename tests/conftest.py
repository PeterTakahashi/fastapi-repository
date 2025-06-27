import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Uuid, Boolean, SmallInteger
from sqlalchemy.orm import declarative_base
from uuid import uuid4
from fastapi_repository import BaseRepository
from faker import Faker

Base = declarative_base()
fake = Faker()

class User(Base):
    __tablename__ = "users"
    id = Column(Uuid, primary_key=True, default=uuid4)
    name = Column(String)
    age = Column(Integer)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    failed_attempts = Column(SmallInteger, default=0)


@pytest.fixture(scope="session")
def engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:")

@pytest_asyncio.fixture(scope="session")
async def tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(engine, tables):
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
async def user_repository(db_session):
    return BaseRepository(db_session, model=User)

@pytest_asyncio.fixture
async def user(db_session):
    user = User(name="Test User", age=30, email=fake.email(), hashed_password="password", is_active=True)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest_asyncio.fixture
async def users(db_session):
    users = [User(name=fake.name(), age=fake.random_int(min=18, max=80), email=fake.email(), hashed_password="password", is_active=True) for _ in range(10)]
    db_session.add_all(users)
    await db_session.commit()
    return users
