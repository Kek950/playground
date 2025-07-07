rec = ('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        class_array TEXT NOT NULL,
        attendance_array TEXT DEFAULT '[]'
    )
    ''')