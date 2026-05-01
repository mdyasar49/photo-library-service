import os
import sqlite3
import mimetypes

# Configuration
BYTECODE_STORAGE = "bytecode_storage"
DATABASE = "photos.db"

def sync():
    if not os.path.exists(BYTECODE_STORAGE):
        print("Storage folder not found.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get existing files in DB
    cursor.execute("SELECT filepath FROM photo")
    existing_paths = {row[0] for row in cursor.fetchall()}
    
    count = 0
    for root, dirs, files in os.walk(BYTECODE_STORAGE):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, BYTECODE_STORAGE)
            
            # Normalize path for DB
            db_path = full_path.replace("\\", "/")
            
            if db_path not in existing_paths:
                print(f"Syncing: {file}")
                # Determine directory name
                parts = rel_path.split(os.sep)
                directory = parts[0] if len(parts) > 1 else ""
                
                # Remove .bin for the display name if present
                clean_name = file.replace(".bin", "")
                
                cursor.execute("""
                    INSERT INTO photo (filename, filepath, url, directory, tags, description, mime_type, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    clean_name,
                    db_path,
                    f"/api/uploads/{clean_name}",
                    directory,
                    "synced",
                    "Automatically synced from storage",
                    mimetypes.guess_type(clean_name)[0] or "image/jpeg"
                ))
                count += 1
    
    conn.commit()
    conn.close()
    print(f"Sync complete. Added {count} new records.")

if __name__ == "__main__":
    sync()
