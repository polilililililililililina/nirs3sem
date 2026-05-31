from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

SECRET_KEY = os.getenv("SECRET_KEY")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

FRONTEND_URL = os.getenv("FRONTEND_URL")

INPUT_DIR = os.getenv("INPUT_DIR", "storage/input")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "storage/output")
AVATAR_DIR = os.getenv("AVATAR_DIR", "storage/avatars")
