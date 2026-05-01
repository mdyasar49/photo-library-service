import os
import binascii
import mimetypes
import zipio
import io
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import zipfile

# Configuration
STORAGE_DIR = "bytecode_storage"
DB_URL = "sqlite:///./photos.db"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Database Setup
Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Photo(Base):
    __tablename__ = "photo"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    url = Column(String)
    directory = Column(String, default="Library")
    tags = Column(JSON, default=[])
    description = Column(Text, default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    mime_type = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bytecode Photo Library API v3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# Helpers
def to_bytecode(binary_data: bytes) -> str:
    return binascii.hexlify(binary_data).decode('utf-8')

def from_bytecode(hex_str: str) -> bytes:
    return binascii.unhexlify(hex_str)

@app.post("/api/photos")
async def upload_photos(
    photos: List[UploadFile] = File(...),
    directory: str = Form("Library"),
    tags: str = Form(""),
    description: str = Form("")
):
    db = SessionLocal()
    uploaded = []
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    clean_dir = directory.strip() or "Library"
    
    for file in photos:
        content = await file.read()
        hex_content = to_bytecode(content)
        
        # Store as .bin bytecode
        storage_filename = f"{file.filename}.bin"
        storage_path = os.path.join(STORAGE_DIR, storage_filename)
        
        with open(storage_path, "w") as f:
            f.write(hex_content)
            
        new_photo = Photo(
            filename=file.filename,
            filepath=storage_path,
            url=f"/api/uploads/{file.filename}",
            directory=clean_dir,
            tags=tag_list,
            description=description,
            mime_type=file.content_type or mimetypes.guess_type(file.filename)[0] or "image/jpeg"
        )
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        uploaded.append(new_photo)
    
    db.close()
    return uploaded

@app.get("/api/photos")
def list_photos(q: Optional[str] = None):
    db = SessionLocal()
    query = db.query(Photo)
    if q:
        query = query.filter(
            (Photo.filename.contains(q)) | 
            (Photo.description.contains(q)) |
            (Photo.directory.contains(q))
        )
    photos = query.order_by(Photo.uploaded_at.desc()).all()
    db.close()
    return photos

@app.get("/api/uploads/{filename}")
def serve_file(filename: str, download: bool = False):
    db = SessionLocal()
    photo = db.query(Photo).filter(Photo.filename == filename).first()
    db.close()
    
    if not photo or not os.path.exists(photo.filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(photo.filepath, "r") as f:
        hex_str = f.read()
    
    binary_data = from_bytecode(hex_str)
    
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{photo.filename}"'
    
    return Response(content=binary_data, media_type=photo.mime_type, headers=headers)

@app.get("/api/photos/directory/{dir_name}/download")
def download_directory(dir_name: str):
    db = SessionLocal()
    # Normalize "Library" to match empty/null directories if needed
    photos = db.query(Photo).filter(Photo.directory == dir_name).all()
    if not photos and dir_name.lower() == "others":
        photos = db.query(Photo).filter((Photo.directory == "") | (Photo.directory == None)).all()
    db.close()

    if not photos:
        raise HTTPException(status_code=404, detail="Directory empty or not found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for photo in photos:
            if os.path.exists(photo.filepath):
                with open(photo.filepath, "r") as f:
                    content = from_bytecode(f.read())
                zip_file.writestr(photo.filename, content)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer, 
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={dir_name}_export.zip"}
    )

@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    count = db.query(Photo).count()
    
    total_bytes = 0
    for root, dirs, files in os.walk(STORAGE_DIR):
        for f in files:
            total_bytes += os.path.getsize(os.path.join(root, f))
    
    # Estimate raw size (hex is 2x)
    raw_estimate = total_bytes / 2
    size_str = f"{raw_estimate / 1024 / 1024:.2f} MB" if raw_estimate > 1048576 else f"{raw_estimate / 1024:.2f} KB"
    
    db.close()
    return {
        "total_photos": count,
        "total_size": size_str,
        "version": "3.0.0",
        "codename": "Bytecode Shield"
    }

@app.get("/api/photos/{photo_id}/hex")
def get_hex(photo_id: int):
    db = SessionLocal()
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    db.close()
    if not photo: raise HTTPException(status_code=404)
    with open(photo.filepath, "r") as f:
        return {"hex": f.read()[:5000] + "... [TRUNCATED]"}

@app.post("/api/photos/sync")
def sync_storage():
    import subprocess
    subprocess.run(["python", "sync_storage.py"])
    return {"message": "Sync triggered"}

@app.delete("/api/photos/{photo_id}")
def delete_photo(photo_id: int):
    db = SessionLocal()
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo:
        if os.path.exists(photo.filepath):
            os.remove(photo.filepath)
        db.delete(photo)
        db.commit()
    db.close()
    return {"status": "deleted"}

@app.post("/api/photos/bulk-delete")
def bulk_delete(data: dict):
    db = SessionLocal()
    ids = data.get("ids", [])
    photos = db.query(Photo).filter(Photo.id.in_(ids)).all()
    for photo in photos:
        if os.path.exists(photo.filepath):
            os.remove(photo.filepath)
        db.delete(photo)
    db.commit()
    db.close()
    return {"status": "success", "count": len(photos)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
