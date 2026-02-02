# AESP Backend

> API server cho nền tảng luyện nói tiếng Anh với AI - FastAPI + PostgreSQL + Google Gemini

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini AI"/>
</p>

---

## Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/AESP-T12-2025/aesp-backend.git
cd aesp-backend

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env  # Edit with your credentials

# 5. Run server
uvicorn app.main:app --reload
```

🌐 Server: http://localhost:8000  
📚 API Docs: http://localhost:8000/docs

---

## Features

| Feature | Description |
|---------|-------------|
| 🔐 **Authentication** | JWT + OAuth Google login |
| 👥 **User Roles** | Learner, Mentor, Admin with RBAC |
| 📚 **Content** | Categories → Topics → Scenarios → Vocabulary |
| 🤖 **AI Services** | Chat, Speech Analysis, Feedback (Gemini) |
| 🔊 **TTS** | Text-to-Speech with Edge TTS |
| 📊 **Proficiency Test** | 20-question placement test |
| 👥 **Peer Practice** | WebRTC voice chat matching |
| 👨‍🏫 **Mentor System** | Booking, assessments, reviews |
| 💳 **Payments** | Package subscriptions, transactions |
| 🏆 **Gamification** | XP, Streaks, Challenges, Leaderboard |
| 🔔 **Notifications** | Push + in-app notifications |
| 📈 **Analytics** | Learning reports, admin dashboard |

---

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SECRET_KEY` | JWT signing key | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `CLOUDINARY_*` | Media upload credentials | ✅ |
| `ALGORITHM` | JWT algorithm (default: HS256) | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 30) | ❌ |

---

## Project Structure

```
aesp-backend/
├── app/
│   ├── core/           # Config, database, security, dependencies
│   ├── models/         # SQLAlchemy ORM (15 modules)
│   ├── routers/        # API endpoints (21 routers)
│   ├── schemas/        # Pydantic validation
│   ├── services/       # Business logic (AI, TTS, notifications)
│   └── main.py         # FastAPI entry point
├── scripts/
│   └── create_admin.py # Admin account management
├── tests/              # Pytest test suite (23 files)
├── requirements.txt    # Python dependencies
└── pytest.ini          # Test configuration
```

---

## API Reference

### Core Endpoints

| Router | Path | Description |
|--------|------|-------------|
| Auth | `/auth/*` | Register, login, OAuth, me |
| Users | `/users/*` | Profile management |
| Content | `/content/*` | Categories, topics, scenarios |
| AI | `/ai/*` | Chat, analyze, TTS, feedback |
| Proficiency | `/proficiency/*` | Placement tests |
| Peer | `/peer/*` | Peer matching, sessions |
| Mentor | `/mentor/*` | Slots, bookings, assessments |
| Learner | `/learner/*` | Learning paths, progress |
| Payment | `/payment/*` | Packages, transactions |
| Analytics | `/analytics/*` | Reports, stats, exports |
| Notifications | `/notifications/*` | Push, in-app alerts |
| Social | `/social/*` | Posts, comments |
| Gamification | `/gamification/*` | XP, challenges, leaderboard |

📚 Full API documentation: http://localhost:8000/docs

---

## Scripts

```bash
# Create admin account
python scripts/create_admin.py
```

---

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app

# Specific test file
pytest tests/test_auth.py -v
```

---

## Deployment

- **Platform**: Render
- **Production**: https://aesp-backend.onrender.com
- **API Docs**: https://aesp-backend.onrender.com/docs

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| PostgreSQL | Database |
| Pydantic | Validation |
| Google Gemini | AI services |
| Edge TTS | Text-to-Speech |
| Cloudinary | Media storage |
| Pytest | Testing |

---

## License

Educational project - UTH (University of Transport Ho Chi Minh City)

---

<p align="center">Made with ❤️ by AESP Team</p>
