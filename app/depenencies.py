from functools import lru_cache
from fastapi import Depends, Cookie, HTTPException
from app.worker import conn
from rq import Queue
from app import config
import motor.motor_asyncio


@lru_cache()
def get_settings():
    return config.Settings()


async def get_db(settings: config.Settings = Depends(get_settings)):
    db_conn = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
    return db_conn.vanguard_db


async def verify_session_cookie(db=Depends(get_db), session_id: str = Cookie(None)):
    if (tournament := await db["tournaments"].find_one({"session_id": session_id})) is not None:
        return tournament

    raise HTTPException(status_code=404, detail=f"Invalid session: {session_id}")


async def get_q():
    return Queue(connection=conn)
