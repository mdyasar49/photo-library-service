# 📸 Photo Library API - Version 2.0

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

A high-performance, asynchronous photo management backend designed for the V2.0 Photo Library ecosystem. Built with a focus on speed, scalability, and ease of use.

## 🚀 Key Features
- **⚡ Asynchronous Architecture**: Leveraging FastAPI for non-blocking I/O and rapid response times.
- **📁 Smart Directory Management**: Organize photos into virtual directories with bulk-delete capabilities.
- **🔍 Advanced Search**: Instant filtering across tags, descriptions, filenames, and directories.
- **🛠️ Automated Documentation**: Interactive Swagger (OpenAPI) and Redoc UI available out of the box.
- **🖼️ Static Asset Streaming**: Efficiently serves high-resolution images via dedicated streaming endpoints.

## 🛠️ Technology Stack
| Layer | Technology |
| :--- | :--- |
| **Framework** | FastAPI |
| **Server** | Uvicorn |
| **Database** | SQLite |
| **ORM** | SQLAlchemy 2.0 |
| **Validation** | Pydantic V2 |

## ⚙️ Installation & Setup

### 1. Environment Preparation
```bash
# Clone the repository
git clone https://github.com/mdyasar49/photo-library-service.git
cd photo-library-service

# Initialize Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Unix/macOS
```

### 2. Dependency Management
```bash
pip install -r requirements.txt
```

### 3. Launch the Server
```bash
python app.py
```

## 📖 API Documentation
Once the server is running, explore the API endpoints:
- **Swagger UI**: [http://localhost:5000/docs](http://localhost:5000/docs)
- **Redoc**: [http://localhost:5000/redoc](http://localhost:5000/redoc)

---
*Developed as part of the Photo Library V2.0 Suite.*
