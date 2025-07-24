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
    # Create posts table for Instagram content
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            post_id VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(255) NOT NULL,
            caption TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        );
    """)
    # Create articles table for RSS feed content
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            headline TEXT NOT NULL,
            source_name VARCHAR(255) NOT NULL,
            summary TEXT,
            published_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() at time zone 'utc')
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

def article_exists(url):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM articles WHERE url = %s", (url,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_article(url, headline, source_name, summary, published_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (url, headline, source_name, summary, published_at) VALUES (%s, %s, %s, %s, %s)",
        (url, headline, source_name, summary, published_at)
    )
    conn.commit()
    cur.close()
    conn.close()