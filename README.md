# AI-Supported English Speaking Platform (AESP) - Backend

Backend API for the AESP project, built with **FastAPI** and **PostgreSQL**.

## 🚀 Features

- **Authentication**: Register/Login with JWT & Bcrypt.
- **User Management**: Profile retrieval and updates.
- **Content Management**: Topics, Categories, Scenarios (Admin CRUD).
- **Media Upload**: Integration with Cloudinary.
- **Mock Payment**: Fake transaction history for testing.
- **Database**: PostgreSQL (Neon Tech) with SQLAlchemy ORM.

## 🛠️ Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy + Pydantic
- PostgreSQL (Neon)
- Cloudinary

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd aesp-backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the root directory with the following variables:
   ```env
   DATABASE_URL=postgresql://<user>:<pass>@<host>/neondb?sslmode=require
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

## ▶️ Running the Server

```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

## 📚 API Documentation

Visit **Swagger UI** to test APIs interactively:
👉 http://127.0.0.1:8000/docs
