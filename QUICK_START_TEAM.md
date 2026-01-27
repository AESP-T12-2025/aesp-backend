# 🚀 Quick Start Guide cho Team

## 📋 Bước 1: Claim Task

1. Vào [GitHub Issues](https://github.com/AESP-T12-2025/aesp-backend/issues)
2. Chọn task (ví dụ: `[HIGH] REQ-ADMIN-2: Enable/Disable Account Toggle`)
3. Comment: **"I'll take this"**
4. Assign issue cho mình

---

## 💻 Bước 2: Setup Local

```bash
# Clone repo
git clone https://github.com/AESP-T12-2025/aesp-backend.git
cd aesp-backend

# Create branch
git checkout -b feature/REQ-ADMIN-2-enable-disable-account

# Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run tests để xem test hiện tại
pytest tests/unit/test_requirements.py::TestAdminRequirements::test_admin_enable_disable_account -v
```

**Kết quả mong đợi:**
```
test_admin_enable_disable_account SKIPPED (Endpoint not implemented - PENDING)
```

---

## 🔧 Bước 3: Implement Feature

### Ví dụ: REQ-ADMIN-2 Enable/Disable Account

**File:** `app/routers/admin.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_admin
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.put("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Toggle user account status (enable/disable).
    
    Requires: Admin role
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Toggle status
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    status = "activated" if user.is_active else "deactivated"
    return {
        "message": f"User {status} successfully",
        "user_id": user.user_id,
        "is_active": user.is_active
    }
```

---

## 🧪 Bước 4: Test Locally

```bash
# Run specific test
pytest tests/unit/test_requirements.py::TestAdminRequirements::test_admin_enable_disable_account -v

# Run all admin tests
pytest tests/unit/test_admin.py -v

# Run all tests
pytest tests/ -v
```

**Kết quả mong đợi:**
```
test_admin_enable_disable_account PASSED ✅
```

---

## 📤 Bước 5: Commit & Push

```bash
# Stage changes
git add app/routers/admin.py

# Commit với format chuẩn
git commit -m "feat(admin): implement enable/disable account toggle

- Add PUT /admin/users/{user_id}/toggle-status endpoint
- Add admin authorization check
- Update test_admin_enable_disable_account to PASS
- Closes #1"

# Push to GitHub
git push origin feature/REQ-ADMIN-2-enable-disable-account
```

---

## 🔀 Bước 6: Create Pull Request

### 6.1 Tạo PR trên GitHub

1. Vào repo trên GitHub
2. Click **"Compare & pull request"**
3. Base: `official` ← Compare: `feature/REQ-ADMIN-2-enable-disable-account`
4. Fill in template:

```markdown
## 📋 Changes

Implement REQ-ADMIN-2: Enable/Disable Account Toggle

Implements: #1

---

## ✅ Checklist

- [x] Tests added/updated
- [x] All tests passing locally
- [x] Code follows style guide
- [x] No print() statements
- [x] Docstrings added

---

## 🧪 Test Results

```bash
pytest tests/unit/test_requirements.py::TestAdminRequirements::test_admin_enable_disable_account -v

PASSED ✅
```

**Tests status:**
- ✅ Passed: 1
- ❌ Failed: 0
```

5. Click **"Create pull request"**

---

## 🤖 Bước 7: Automated Checks

### GitHub sẽ TỰ ĐỘNG:

1. **Chạy tests** (2-3 phút)
2. **Comment kết quả** vào PR:

```
## 🎉 Test Results ✅ PASSED

| Metric | Value |
|--------|-------|
| ✅ Passed | 116 |
| ❌ Failed | 0 |
| ⏭️ Skipped | 23 |
| 📊 Total | 139 |
| 📈 Pass Rate | 83.5% |

✅ All tests passed! Ready to merge.
```

3. **Hiện status** trên PR:
   - ✅ **All checks passed** → Có thể merge
   - ❌ **Some checks failed** → CHẶN merge, phải fix

---

## ❌ Nếu Tests Fail

### GitHub sẽ comment:

```
## ⚠️ Test Results ❌ FAILED

| Metric | Value |
|--------|-------|
| ✅ Passed | 115 |
| ❌ Failed | 1 |

### ❌ Failed Tests

- `tests/unit/test_admin.py::test_admin_enable_disable_account`
  ```
  AssertionError: assert 404 == 200
  ```

❌ Tests failed. Please fix before merging.
```

### Fix và push lại:

```bash
# Fix code
# ...

# Commit fix
git add .
git commit -m "fix: correct endpoint path"
git push origin feature/REQ-ADMIN-2-enable-disable-account
```

**GitHub sẽ TỰ ĐỘNG chạy lại tests!**

---

## ✅ Bước 8: Merge

### Khi tests PASS:

1. Request review từ team lead
2. Chờ approval (1 approval required)
3. Click **"Squash and merge"**
4. Delete branch

```bash
# Local cleanup
git checkout official
git pull origin official
git branch -d feature/REQ-ADMIN-2-enable-disable-account
```

---

## 🎯 Tips

### ✅ DO:
- Chạy tests local trước khi push
- Follow commit message format: `[type]: description`
- Keep PRs small (1 feature = 1 PR)
- Add docstrings
- Use logging instead of print()

### ❌ DON'T:
- Push directly to `main` or `official`
- Create PR without tests
- Ignore failed tests
- Use `print()` statements
- Skip code review

---

## 🆘 Common Issues

### Issue: Tests pass locally but fail on GitHub

**Solution:**
```bash
# Make sure using same Python version
python --version  # Should be 3.11

# Make sure all dependencies installed
pip install -r requirements.txt

# Run tests exactly like GitHub does
pytest tests/ -v --tb=short
```

### Issue: Can't push to branch

**Solution:**
```bash
# Pull latest changes first
git pull origin feature/your-branch-name

# Then push
git push origin feature/your-branch-name
```

### Issue: Merge conflicts

**Solution:**
```bash
# Update from official
git checkout official
git pull origin official

# Rebase your branch
git checkout feature/your-branch-name
git rebase official

# Resolve conflicts, then
git add .
git rebase --continue
git push origin feature/your-branch-name --force
```

---

## 📚 Resources

- [Full Contributing Guide](./CONTRIBUTING.md)
- [Task List](./TASKS.md)
- [GitHub Setup](./SETUP_GITHUB.md)
- [Test Report](./docs/test_report.md)
