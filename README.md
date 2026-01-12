<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini AI"/>
</p>

<h1 align="center">🎓 AESP Backend</h1>
<h3 align="center">AI-Supported English Speaking Practice Platform</h3>

<p align="center">
  <strong>Nền tảng luyện nói tiếng Anh thông minh với sự hỗ trợ của AI</strong>
</p>

---

## 📖 Giới thiệu

**AESP Backend** là hệ thống API server được xây dựng bằng **FastAPI**, cung cấp các dịch vụ RESTful cho nền tảng luyện nói tiếng Anh. Hệ thống tích hợp **AI Gemini** để phân tích và hỗ trợ người học cải thiện kỹ năng Speaking.

### ✨ Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| 🔐 **Authentication** | Đăng ký, đăng nhập với JWT Token bảo mật |
| 👤 **User Management** | Quản lý profile, avatar, phân quyền (Learner/Mentor/Admin) |
| 📚 **Content Management** | CRUD cho Categories, Topics, Scenarios, Vocabulary |
| 🤖 **AI Integration** | Chat AI, phân tích phát âm với Google Gemini |
| 🔊 **Text-to-Speech** | Chuyển văn bản thành giọng nói với Edge TTS |
| ☁️ **Media Upload** | Upload ảnh/audio lên Cloudinary |
| 💳 **Payment** | Quản lý giao dịch thanh toán |
| 🌐 **Social Features** | Bài viết, bình luận, tương tác cộng đồng |

---

## 🗂️ Cấu trúc dự án

```
aesp-backend/
├── app/
│   ├── core/           # Cấu hình database, security, settings
│   ├── models/         # SQLAlchemy ORM models
│   ├── routers/        # API endpoints (auth, users, content, ai, etc.)
│   ├── schemas/        # Pydantic schemas cho validation
│   ├── services/       # Business logic (AI service, TTS service)
│   └── main.py         # Application entry point
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu hệ thống

- **Python** 3.10+
- **PostgreSQL** (hoặc sử dụng Neon DB cloud)

### Bước 1: Clone repository

```bash
git clone https://github.com/AESP-T12-2025/aesp-backend.git
cd aesp-backend
```

### Bước 2: Tạo môi trường ảo

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc:

```env
# Database
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# JWT Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary (Media Upload)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Google Gemini AI (Optional)
GEMINI_API_KEY=your-gemini-api-key
```

### Bước 5: Khởi động server

```bash
uvicorn app.main:app --reload
```

🌐 Server chạy tại: `http://localhost:8000`

📚 API Documentation: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### 🔐 Authentication
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/auth/register` | Đăng ký tài khoản mới |
| POST | `/auth/login` | Đăng nhập, nhận JWT token |
| GET | `/auth/me` | Thông tin user hiện tại |

### 👥 Users
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/users` | Danh sách users (Admin) |
| GET | `/users/{id}` | Chi tiết user |
| PUT | `/users/profile` | Cập nhật profile |

### 📖 Content
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/categories` | Danh sách categories |
| GET | `/topics` | Danh sách topics |
| GET | `/scenarios` | Danh sách scenarios |
| GET | `/scenarios/{id}/vocab` | Từ vựng theo scenario |

### 🤖 AI Services
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/ai/chat` | Chat với AI assistant |
| POST | `/ai/analyze` | Phân tích bài nói |
| POST | `/ai/tts` | Text-to-Speech |

### 📤 Upload
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/upload/image` | Upload hình ảnh |
| POST | `/upload/audio` | Upload file audio |

---

## 🔧 Tech Stack

| Công nghệ | Mục đích |
|-----------|----------|
| **FastAPI** | Web framework |
| **SQLAlchemy** | ORM |
| **PostgreSQL** | Database |
| **Pydantic** | Data validation |
| **JWT** | Authentication |
| **Cloudinary** | Media storage |
| **Google Gemini** | AI/ML services |
| **Edge TTS** | Text-to-Speech |

---

## 🚢 Deployment

Backend được deploy trên **Render**:

🔗 Production URL: `https://aesp-backend.onrender.com`

---

## 👥 Team

| Thành viên | Vai trò |
|------------|---------|
| **Bùi Quang Long** | Team Leader |

---

## 📄 License

Dự án này được phát triển cho mục đích học tập tại **UTH - ĐẠI HỌC **.

---

<p align="center">
  <sub>Made with ❤️ by AESP Team</sub>
</p>
