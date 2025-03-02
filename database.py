# database.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set.")

engine = create_async_engine(
    DATABASE_URL, echo=True, isolation_level="READ COMMITTED"
)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
