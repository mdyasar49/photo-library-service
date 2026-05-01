import os
import sqlite3
import mimetypes
from datetime import datetime

STORAGE_DIR = "bytecode_storage"
DB_PATH = "photos.db"

def sync():
    if not os.path.exists(STORAGE_DIR):
        print("Storage dir not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure mime_type column exists
    try:
        cursor.execute("ALTER TABLE photo ADD COLUMN mime_type TEXT")
    except:
        pass

    count = 0
    for root, dirs, files in os.walk(STORAGE_DIR):
        for file in files:
            if not file.endswith(".bin"):
                continue
                
            clean_name = file[:-4] # Remove .bin
            db_path = os.path.join(root, file).replace("\\", "/")
            
            # Check if exists
            cursor.execute("SELECT id FROM photo WHERE filename = ?", (clean_name,))
            if not cursor.fetchone():
                directory = os.path.basename(root) if root != STORAGE_DIR else "Library"
                
                cursor.execute("""
                    INSERT INTO photo (filename, filepath, url, directory, tags, description, mime_type, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    clean_name,
                    db_path,
                    f"/api/uploads/{clean_name}",
                    directory,
                    '["synced"]',
                    "Automatically synced from storage",
                    mimetypes.guess_type(clean_name)[0] or "image/jpeg"
                ))
                count += 1
    
    conn.commit()
    conn.close()
    print(f"Sync complete. Added {count} new records.")

if __name__ == "__main__":
    sync()
