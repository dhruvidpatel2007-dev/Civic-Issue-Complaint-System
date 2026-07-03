import sqlite3

conn = sqlite3.connect("complaints.db")

cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN role TEXT DEFAULT 'user'
    """)

    conn.commit()

    print("Role column added successfully!")

except Exception as e:
    print("Error:", e)

conn.close()