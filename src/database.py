from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
from .config import settings

engine = create_engine(url=settings.database_url, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    latency_ms = Column(Float)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)
