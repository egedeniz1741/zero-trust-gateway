import os

JWT_SECRET = os.getenv("JWT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_USER = os.getenv("INITIAL_ADMIN_USER")
ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
ALGORITHM = "HS256"