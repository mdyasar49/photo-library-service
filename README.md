# photo-library-service

---

# 📷 Photo Library Application

## 🚀 Overview

This is a **Photo Library Application** built with:

* **Backend:** Python (Flask + SQLAlchemy + SQLite)
* **Frontend:** React (Axios + Material-ui + ESlint)
* **Database:** SQLite (`photos.db`)

The app allows users to:

* Upload, edit, and delete photos
* Organize photos into directories
* Add tags and descriptions
* Search photos by tags, descriptions, filenames, or directories
* Serve uploaded images through a dedicated endpoint

---

## 📂 Project Structure

```
photo-library-backend/
│
├── app.py           # Flask backend with REST APIs
├── models.py        # SQLAlchemy Photo model
├── photos.db        # SQLite database
├── view_db.py       # Utility script to view DB contents
├── uploads/         # Uploaded photo files
└── requirements.txt # Python dependencies
```

---

## 🛠️ Setup Instructions

### 1️⃣ Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

Backend will run at: **[http://localhost:5000](http://localhost:5000)**

---

### 2️⃣ API Endpoints

| Method | Endpoint                       | Description                     |
| ------ | ------------------------------ | ------------------------------- |
| GET    | `/api/photos`                  | List all photos                 |
| POST   | `/api/photos`                  | Upload new photo(s)             |
| GET    | `/api/photos/<id>`             | Get photo by ID                 |
| PUT    | `/api/photos/<id>`             | Update photo (tags/description) |
| DELETE | `/api/photos/<id>`             | Delete photo                    |
| GET    | `/api/photos/search?q=keyword` | Search photos                   |
| DELETE | `/api/photos/directory/<name>` | Delete all photos in directory  |
| GET    | `/api/uploads/<filename>`      | Access uploaded image           |

---

## 📊 Database Schema

Database: **SQLite (`photos.db`)**

**Table: `photo`**

| Column       | Type       | Description             |
| ------------ | ---------- | ----------------------- |
| id           | INTEGER PK | Unique photo ID         |
| filename     | TEXT       | Name of uploaded file   |
| filepath     | TEXT       | Absolute path to file   |
| url          | TEXT       | API-accessible URL      |
| directory    | TEXT       | Directory name (if any) |
| tags         | TEXT       | Comma-separated tags    |
| description  | TEXT       | Photo description       |
| uploaded\_at | DATETIME   | Timestamp of upload     |

---

## 🤖 AI Prompts and Models

* No AI prompts or models are included.
* If AI functionality is added later, provide model files or prompt sets separately.

---

## ✅ Deliverables

1. **Complete Source Code** – Flask backend (`app.py`, `models.py`, etc.)
2. **Database Schema** – SQLite schema (`photos.db`, `view_db.py`)
3. **AI Prompts/Models (if applicable)** – No AI prompts or models are included.

---
