from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from typing import Any, AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from .config import settings

class DatabaseSessionManager:
    def __init__(self, url, engine_kwargs: dict[str, Any]={}):
        self._engine = create_async_engine(url, **engine_kwargs)
        self._session = async_sessionmaker(bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        
        await self._engine.dispose()

        self._engine = None
        self._session = None
    
    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        
        async with self._engine.begin() as connection:
            try: 
                yield connection
            
            except Exception:
                await connection.rollback()
                raise

    
    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        
        session = self._session()

        try: 
            yield session
        except Exception:
            await session.rollback()
            raise 
        finally:
            await session.close()


session_manager = DatabaseSessionManager(url=settings.database_url)

async def get_db_session():
    async with session_manager.session() as session:
        yield session 

async def init_db():
    async with session_manager.connect() as connection:
        await connection.run_sync(Base.metadata.create_all)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class CallLog(Base):
    __tablename__ = "CallLog"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    latency_ms = Column(Float)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
