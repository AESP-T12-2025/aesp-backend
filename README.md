# 🚀 AESP Backend - AI-Supported English Speaking Platform

**Version:** 1.0 (Week 1 Official Release)  
**Status:** ✅ 100% Complete  
**Developed by:** Bùi Quang Long (Leader)

---

## 🌟 Giới thiệu

Đây là Backend chính thức cho dự án AESP, được xây dựng bằng **FastAPI** và **PostgreSQL**. Hệ thống cung cấp đầy đủ các API cần thiết cho Frontend (Next.js) hoạt động, bao gồm xác thực, quản lý nội dung, upload media và giả lập thanh toán.

### 🔥 Tính năng nổi bật (Đã hoàn thiện)
*   **Authentication**: Đăng ký/Đăng nhập bảo mật chuẩn JWT (Access Token).
*   **User Profile**: Quản lý thông tin cá nhân, cập nhật Avatar.
*   **Content Management**:
    *   Hiển thị Danh mục (Categories), Chủ đề (Topics), Bài học (Scenarios).
    *   **Admin Tools**: API Thêm/Sửa/Xóa bài học (Full CRUD).
*   **Media Service**: Tích hợp **Cloudinary** để upload ảnh cực nhanh.
*   **Features for Frontend**:
    *   **CORS Config**: Đã mở kết nối cho localhost:3000.
    *   **Mock Payment**: API giả lập lịch sử giao dịch.
    *   **Vocabulary**: API lấy từ vựng theo bài học.
    *   **Practice Session**: API lưu kết quả luyện tập Speaking.

---

## 🛠️ Hướng dẫn Cài đặt (Dành cho Dev)

### 1. Clone dự án
```bash
git clone https://github.com/AESP-T12-2025/aesp-backend.git
cd aesp-backend
```

### 2. Thiết lập môi trường (Virtual Environment)
*   **Windows:**
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **Mac/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 4. Cấu hình file `.env` (Quan trọng!)
Tạo file `.env` ở thư mục gốc và dán nội dung sau (Key đã được cấu hình sẵn cho Dev):

```env
# Database (Neon Postgres - Live)
DATABASE_URL=postgresql://neondb_owner:npg_AmkzWlJcTf12@ep-noisy-smoke-a15epwsb-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Security
SECRET_KEY=changethisSecretKeyOnlyForDev
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary (Media Upload - Upload được luôn)
CLOUDINARY_CLOUD_NAME=dujyahhwk
CLOUDINARY_API_KEY=969531162213173
CLOUDINARY_API_SECRET=03SY3A46cdIfcR2wH1RWMQz0HlI
```

---

## ▶️ Chạy Server

Chạy lệnh sau để khởi động Backend:

```powershell
uvicorn app.main:app --reload
```

*   Server sẽ chạy tại: `http://127.0.0.1:8000`
*   **API Docs (Swagger UI):** 👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    *(Vào đây để test toàn bộ API trực quan, không cần Postman)*

---

## 📚 Hướng dẫn sử dụng API (Quick Cheatsheet)

### 1. Đăng ký & Đăng nhập (Auth)
*   Vào `POST /auth/register` để tạo tài khoản mới.
*   Vào `POST /auth/login` để đăng nhập -> Copy **Access Token** trả về.
*   **Quan trọng**: Bấm nút **Authorize (ổ khóa)** trên Swagger -> Nhập `Bearer <token_vua_copy>` để mở khóa các API bảo mật.

### 2. Upload Ảnh (Media)
*   Dùng API `POST /upload/image`. Chọn file ảnh từ máy -> Trả về URL dùng luôn được.

### 3. Test tính năng Admin (Thêm bài học)
*   *Lưu ý*: Hiện tại check quyền Admin đang được **TẮT** (commented out) để Frontend dễ dàng dev tính năng mà không cần chỉnh DB.
*   Cứ gọi `POST /topics` hoặc `POST /scenarios` thoải mái.
*   **Payload mẫu cho tạo Speaking Session**:
    ```json
    {
      "scenario_id": 1,
      "start_time": "2026-01-04T12:00:00"
    }
    ```

### 4. Từ vựng (Vocabulary)
*   Gọi `GET /scenarios/{id}/vocab` để lấy list từ vựng gợi ý.

---

## 🤝 Liên hệ
Leader: **Bùi Quang Long**
*(Nếu server lỗi hoặc DB sập, vui lòng ping trực tiếp)*
