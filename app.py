import os
import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import List, Optional

app = FastAPI(title="Photo Library API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BYTECODE_STORAGE = os.path.join(BASE_DIR, 'bytecode_storage')
os.makedirs(BYTECODE_STORAGE, exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///./photos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Photo(Base):
    __tablename__ = "photo"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    url = Column(String, nullable=False)
    directory = Column(String, default="")
    tags = Column(String, default="")
    description = Column(String, default="")
    mime_type = Column(String, default="image/jpeg")
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "url": self.url,
            "directory": self.directory,
            "tags": [t.strip() for t in self.tags.split(',')] if self.tags else [],
            "description": self.description,
            "uploaded_at": self.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if self.uploaded_at else None
        }

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/photos")
def get_photos(db: Session = Depends(get_db)):
    photos = db.query(Photo).order_by(Photo.uploaded_at.desc()).all()
    return [p.to_dict() for p in photos]

@app.post("/api/photos", status_code=201)
async def upload_photos(
    photos: List[UploadFile] = File(...),
    directory: str = Form(""),
    tags: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    results = []
    for photo in photos:
        filename = photo.filename
        # Path-wise bytecode storage
        target_dir = os.path.join(BYTECODE_STORAGE, directory) if directory else BYTECODE_STORAGE
        os.makedirs(target_dir, exist_ok=True)
        
        bytecode_path = os.path.join(target_dir, f"{filename}.bin")
        
        content = await photo.read()
        hex_content = content.hex() # Convert binary to hex string
        
        with open(bytecode_path, "w") as f:
            f.write(hex_content)
            
        url = f"/api/uploads/{filename}"
        new_photo = Photo(
            filename=filename,
            filepath=bytecode_path,
            url=url,
            directory=directory,
            tags=tags,
            description=description,
            mime_type=photo.content_type or "image/jpeg"
        )
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        results.append(new_photo.to_dict())
        
    return results

@app.put("/api/photos/{photo_id}")
async def update_photo(
    photo_id: int,
    tags: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    p = db.query(Photo).filter(Photo.id == photo_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    if photo:
        filename = photo.filename
        dir_path = os.path.join(BYTECODE_STORAGE, p.directory) if p.directory else BYTECODE_STORAGE
        os.makedirs(dir_path, exist_ok=True)
        bytecode_path = os.path.join(dir_path, f"{filename}.bin")
        
        content = await photo.read()
        hex_content = content.hex()
        with open(bytecode_path, "w") as buffer:
            buffer.write(hex_content)
        
        try:
            if os.path.exists(p.filepath):
                os.remove(p.filepath)
        except Exception:
            pass
            
        p.filename = filename
        p.filepath = bytecode_path
        p.url = f"/api/uploads/{filename}"
        p.mime_type = photo.content_type or "image/jpeg"
        
    if tags is not None:
        p.tags = tags
    if description is not None:
        p.description = description
        
    db.commit()
    db.refresh(p)
    return p.to_dict()

@app.post("/api/photos/bulk-delete", status_code=204)
def bulk_delete_photos(payload: dict, db: Session = Depends(get_db)):
    photo_ids = payload.get("ids", [])
    if not photo_ids:
        return None
        
    photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
    for p in photos:
        try:
            if os.path.exists(p.filepath):
                os.remove(p.filepath)
        except Exception:
            pass
        db.delete(p)
    db.commit()
    return None

@app.delete("/api/photos/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    p = db.query(Photo).filter(Photo.id == photo_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    try:
        if os.path.exists(p.filepath):
            os.remove(p.filepath)
    except Exception:
        pass
        
    db.delete(p)
    db.commit()
    return None

@app.delete("/api/photos/directory/{directory_name:path}", status_code=204)
def delete_directory(directory_name: str, db: Session = Depends(get_db)):
    if directory_name.lower() in ['library', 'others']:
        photos = db.query(Photo).filter((Photo.directory == 'others') | (Photo.directory == 'Library') | (Photo.directory == '') | (Photo.directory == None)).all()
    else:
        photos = db.query(Photo).filter(Photo.directory == directory_name).all()
        
    for p in photos:
        try:
            if os.path.exists(p.filepath):
                os.remove(p.filepath)
        except Exception:
            pass
        db.delete(p)
    db.commit()
    return None

@app.get("/api/photos/search")
def search_photos(q: str = "", db: Session = Depends(get_db)):
    if not q:
        return []
    q_lower = q.lower()
    results = db.query(Photo).filter(
        Photo.tags.ilike(f'%{q_lower}%') |
        Photo.description.ilike(f'%{q_lower}%') |
        Photo.filename.ilike(f'%{q_lower}%') |
        Photo.directory.ilike(f'%{q_lower}%')
    ).order_by(Photo.uploaded_at.desc()).all()
    return [r.to_dict() for r in results]

@app.get("/api/photos/{photo_id}/hex")
def get_photo_hex(photo_id: int, db: Session = Depends(get_db)):
    p = db.query(Photo).filter(Photo.id == photo_id).first()
    if not p or not os.path.exists(p.filepath):
        raise HTTPException(status_code=404, detail="Photo or file not found")
    
    try:
        with open(p.filepath, "r") as f:
            content = f.read(1024).strip()
            # If it's already hex, format it
            if all(c in '0123456789abcdefABCDEF' for c in content[:10]):
                formatted_hex = ' '.join(content[i:i+2] for i in range(0, len(content), 2))
                return {"hex": formatted_hex}
            else:
                raise ValueError("Not hex")
    except Exception:
        with open(p.filepath, "rb") as f:
            content = f.read(512)
            hex_dump = content.hex()
            formatted_hex = ' '.join(hex_dump[i:i+2] for i in range(0, len(hex_dump), 2))
            return {"hex": formatted_hex}

@app.get("/api/photos/{photo_id}")
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    p = db.query(Photo).filter(Photo.id == photo_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Photo not found")
    return p.to_dict()

@app.post("/api/photos/sync")
def sync_storage_api(db: Session = Depends(get_db)):
    import subprocess
    try:
        # Run the sync script
        result = subprocess.run([os.path.join("venv", "Scripts", "python.exe"), "sync_storage.py"], capture_output=True, text=True)
        return {"message": result.stdout.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_photos = db.query(Photo).count()
    total_size = 0
    if os.path.exists(BYTECODE_STORAGE):
        for root, dirs, files in os.walk(BYTECODE_STORAGE):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
                
    # Convert size to readable format
    size_str = f"{total_size / (1024*1024):.2f} MB" if total_size > 1024*1024 else f"{total_size / 1024:.2f} KB"
    
    return {
        "total_photos": total_photos,
        "total_size": size_str,
        "version": "3.0.0",
        "codename": "Bytecode Shield"
    }

@app.get("/api/photos/directory/{directory_name:path}/download")
def download_directory(directory_name: str, db: Session = Depends(get_db)):
    import zipfile
    import io
    
    # Handle default directory naming (Library, others, or empty)
    if directory_name.lower() in ['library', 'others']:
        photos = db.query(Photo).filter((Photo.directory == 'others') | (Photo.directory == 'Library') | (Photo.directory == '') | (Photo.directory == None)).all()
    else:
        photos = db.query(Photo).filter(Photo.directory == directory_name).all()
        
    if not photos:
        raise HTTPException(status_code=404, detail=f"No photos found in directory: {directory_name}")
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for p in photos:
            if os.path.exists(p.filepath):
                try:
                    with open(p.filepath, "r") as f:
                        content = f.read().strip()
                        binary_data = bytes.fromhex(content)
                    zip_file.writestr(p.filename, binary_data)
                except Exception:
                    # Fallback for raw binary
                    with open(p.filepath, "rb") as f:
                        zip_file.writestr(p.filename, f.read())
                        
    zip_buffer.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={directory_name or 'photos'}.zip"}
    )

@app.get("/api/uploads/{filename}")
def serve_file(filename: str, download: bool = False, db: Session = Depends(get_db)):
    # Find the photo in DB
    p = db.query(Photo).filter(Photo.filename == filename).first()
    if not p:
        raise HTTPException(status_code=404, detail="Photo record not found")
        
    if not os.path.exists(p.filepath):
        alt_path = os.path.join(BYTECODE_STORAGE, filename)
        if os.path.exists(alt_path):
            p.filepath = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"Bytecode file not found at {p.filepath}")
    
    try:
        # Check if it's hex or binary
        with open(p.filepath, "rb") as f:
            raw_data = f.read()
            
        try:
            # Try to decode as hex string first
            hex_str = raw_data.decode('utf-8').strip()
            binary_data = bytes.fromhex(hex_str)
        except Exception:
            # If decoding fails, it's already raw binary
            binary_data = raw_data
        
        from fastapi import Response
        import mimetypes
        mime, _ = mimetypes.guess_type(filename)
        headers = {}
        if download:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'
            
        return Response(content=binary_data, media_type=mime or "image/jpeg", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
