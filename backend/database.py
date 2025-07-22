import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ.get("POSTGRES_PORT", 5432)
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            post_id VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(255) NOT NULL,
            caption TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def post_exists(post_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM posts WHERE post_id = %s", (post_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_post(post_id, username, caption, timestamp):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (post_id, username, caption, timestamp) VALUES (%s, %s, %s, %s)",
        (post_id, username, caption, timestamp)
    )
    conn.commit()
    cur.close()
    conn.close()
