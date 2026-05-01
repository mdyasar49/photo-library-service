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
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
            
        url = f"/api/uploads/{filename}"
        new_photo = Photo(
            filename=filename,
            filepath=filepath,
            url=url,
            directory=directory,
            tags=tags,
            description=description
        )
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        results.append(new_photo.to_dict())
        
    return results

@app.get("/api/photos/{photo_id}")
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    p = db.query(Photo).filter(Photo.id == photo_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Photo not found")
    return p.to_dict()

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
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
        
        try:
            if os.path.exists(p.filepath):
                os.remove(p.filepath)
        except Exception:
            pass
            
        p.filename = filename
        p.filepath = filepath
        p.url = f"/api/uploads/{filename}"
        
    if tags is not None:
        p.tags = tags
    if description is not None:
        p.description = description
        
    db.commit()
    db.refresh(p)
    return p.to_dict()

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

@app.delete("/api/photos/directory/{directory_name:path}", status_code=204)
def delete_directory(directory_name: str, db: Session = Depends(get_db)):
    if directory_name.lower() == 'others':
        photos = db.query(Photo).filter((Photo.directory == 'others') | (Photo.directory == '') | (Photo.directory == None)).all()
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

@app.get("/api/uploads/{filename}")
def serve_file(filename: str):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
