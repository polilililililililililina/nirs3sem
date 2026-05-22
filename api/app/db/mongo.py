from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from app.core.config import MONGO_URL, DB_NAME

load_dotenv()

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]