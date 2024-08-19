from datetime import datetime
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, ForeignKey, MetaData, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker

from config.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()

metadata = MetaData()

engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
     Provides an asynchronous SQLAlchemy session generator for database operations.

     This function is intended to be used with dependency injection in FastAPI. It creates a new
     asynchronous SQLAlchemy session, yields it for use in database operations, and ensures that the
     session is properly closed when no longer needed.

     Yields:
         AsyncSession: An asynchronous SQLAlchemy session object that can be used to interact with the database.

     Example usage in a FastAPI route:
         async def some_route(session: AsyncSession = Depends(get_async_session)):
             # Use the session to perform database operations
             pass

     Notes:
         - The function uses a context manager to ensure that the session is closed when it is done.
         - The `AsyncSession` object yielded by this function should be used within the context of a request
           or other asynchronous operation to ensure proper resource management.
     """
    async with async_session_maker() as session:
        yield session