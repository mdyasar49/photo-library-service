import sqlite3

conn = sqlite3.connect('photos.db')
c = conn.cursor()

# Show all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", c.fetchall())

# Show all data in the photo table
c.execute("SELECT * FROM photo;")
rows = c.fetchall()
for row in rows:
    print(row)

conn.close()
