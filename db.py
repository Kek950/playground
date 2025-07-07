import sqlite3
import json
from datetime import datetime
from SQLrec import rec

def init_db():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute(rec)
    conn.commit()
    conn.close()

def add_missing_column():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN attendance_array TEXT DEFAULT '[]'")
        print("✅ Column 'attendance_array' added.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️ Column already exists.")
        else:
            raise e
    conn.commit()
    conn.close()

def get_students(class_name, user_id):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT class_array FROM students WHERE class_name = ? AND user_id = ?', (class_name, user_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return []
    return []
