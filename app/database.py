from app.config import ADMIN_PASSWORD, ADMIN_USER, DATABASE_URL, REDIS_HOST, REDIS_PORT
from passlib.context import CryptContext
import psycopg2
import redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#
redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True
)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    if not DATABASE_URL or not ADMIN_USER or not ADMIN_PASSWORD:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            hashed_password TEXT NOT NULL,
            role VARCHAR(20) NOT NULL
        );
    """)


    admin_pw = pwd_context.hash(ADMIN_PASSWORD)
    cur.execute(
        """
        INSERT INTO users (username, hashed_password, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING;
    """,
        (ADMIN_USER, admin_pw, "admin"),
    )

  
    viewer_pw = pwd_context.hash(ADMIN_PASSWORD)
    cur.execute(
        """
        INSERT INTO users (username, hashed_password, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING;
    """,
        ("guest", viewer_pw, "viewer"),
    )

    conn.commit()
    cur.close()
    conn.close()