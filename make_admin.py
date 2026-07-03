def init_db():
    conn = get_db_connection()
    
    # Complaints table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            file_path TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    """)

    # Users table (FOR LOGIN / REGISTER / FORGOT PASSWORD)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()
