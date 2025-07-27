import os
import psycopg2
from psycopg2 import sql
from psycopg2 import errors
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
    
    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    # Create posts table for Instagram content with user_id
    # Add user_id and composite unique constraint if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            post_id VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            caption TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            UNIQUE (post_id, user_id)
        );
    """)

    # Create articles table for RSS feed content with user_id
    # Add user_id and composite unique constraint if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            headline TEXT NOT NULL,
            source_name VARCHAR(255) NOT NULL,
            summary TEXT,
            published_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() at time zone 'utc'),
            UNIQUE (url, user_id)
        );
    """)

    # Create captions table for saved, stylized captions with user_id
    # Add user_id and composite unique constraint if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS captions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            headline TEXT NOT NULL,
            summary TEXT NOT NULL,
            source_caption TEXT NOT NULL,
            versus_caption TEXT NOT NULL,
            saved_at TIMESTAMP WITH TIME ZONE DEFAULT (now() at time zone 'utc'),
            UNIQUE (headline, user_id)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_user(username, password_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id;",
            (username, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except errors.UniqueViolation:
        conn.rollback()
        return None # User already exists
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def post_exists(post_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM posts WHERE post_id = %s AND user_id = %s;", (post_id, user_id))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_post(post_id, user_id, username, caption, timestamp):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (post_id, user_id, username, caption, timestamp) VALUES (%s, %s, %s, %s, %s);",
        (post_id, user_id, username, caption, timestamp)
    )
    conn.commit()
    cur.close()
    conn.close()

def article_exists(url, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM articles WHERE url = %s AND user_id = %s;", (url, user_id))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_article(url, user_id, headline, source_name, summary, published_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (url, user_id, headline, source_name, summary, published_at) VALUES (%s, %s, %s, %s, %s, %s);",
        (url, user_id, headline, source_name, summary, published_at)
    )
    conn.commit()
    cur.close()
    conn.close()

def save_caption(user_id, headline, summary, source_caption, versus_caption):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO captions (user_id, headline, summary, source_caption, versus_caption) VALUES (%s, %s, %s, %s, %s);",
            (user_id, headline, summary, source_caption, versus_caption)
        )
        conn.commit()
        return True
    except errors.UniqueViolation:
        conn.rollback()
        return False # Caption already exists for this user
    finally:
        cur.close()
        conn.close()

def get_saved_captions(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, headline, summary, source_caption, versus_caption, saved_at FROM captions WHERE user_id = %s ORDER BY saved_at DESC;", (user_id,))
    captions = cur.fetchall()
    cur.close()
    conn.close()
    return captions

def delete_caption(caption_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM captions WHERE id = %s AND user_id = %s;", (caption_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
