# Photo Library API (V2.0)

A modern, high-performance backend for the Photo Library application, built with **FastAPI** and **SQLAlchemy**.

## Tech Stack
- **Framework**: FastAPI
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Server**: Uvicorn

## Features
- Fully asynchronous API endpoints.
- Automatic Swagger documentation.
- Efficient photo management and directory-based deletion.
- Integrated search functionality.

## Setup Instructions

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

The backend will run at: **[http://localhost:5000](http://localhost:5000)**
You can view the interactive API docs at: **[http://localhost:5000/docs](http://localhost:5000/docs)**
