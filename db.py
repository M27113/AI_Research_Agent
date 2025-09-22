# db.py
import sqlite3
from datetime import datetime
import json

DB_FILE = "reports.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            summary TEXT,
            titles TEXT,
            urls TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_report(query, summary, titles=None, urls=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    titles_str = json.dumps(titles) if titles else "[]"
    urls_str = json.dumps(urls) if urls else "[]"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO reports (query, summary, titles, urls, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (query, json.dumps(summary), titles_str, urls_str, timestamp))
    conn.commit()
    conn.close()

def get_reports():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, query, timestamp FROM reports ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_report_by_id(report_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT query, summary, titles, urls FROM reports WHERE id=?", (report_id,))
    row = c.fetchone()
    conn.close()
    if row:
        titles = json.loads(row[2]) if row[2] else []
        urls = json.loads(row[3]) if row[3] else []
        summary = json.loads(row[1]) if row[1] else []
        return {
            "query": row[0],
            "summary": summary,
            "titles": titles,
            "urls": urls
        }
    return None
