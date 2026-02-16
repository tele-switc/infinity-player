import sqlite3
import json
from datetime import datetime

DB_PATH = "contents.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 内容表
    c.execute('''
        CREATE TABLE IF NOT EXISTS contents (
            id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            url TEXT UNIQUE,
            thumbnail TEXT,
            duration INTEGER,
            played BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库已初始化: {DB_PATH}")

def add_content(data):
    """插入新内容，如果存在则忽略"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO contents (id, source, title, url, thumbnail, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['id'], data['source'], data['title'], data['url'], data['thumbnail'], data['duration']))
        conn.commit()
        return c.rowcount > 0 # 返回是否插入了新数据
    finally:
        conn.close()

def get_unplayed():
    conn = get_db_connection()
    contents = conn.execute('SELECT * FROM contents WHERE played = 0').fetchall()
    conn.close()
    return [dict(row) for row in contents]

def mark_played(content_id):
    conn = get_db_connection()
    conn.execute('UPDATE contents SET played = 1 WHERE id = ?', (content_id,))
    conn.commit()
    conn.close()
