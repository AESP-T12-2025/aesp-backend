# 🤝 Contributing to AESP Backend

## 📋 Workflow

### 1. Pick a Task

1. Vào [GitHub Issues](https://github.com/AESP-T12-2025/aesp-backend/issues)
2. Chọn issue chưa có người làm (không có assignee)
3. Comment "I'll take this" và assign cho mình
4. Chuyển issue sang "In Progress" trên Project Board

### 2. Create Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/REQ-XXX-feature-name

# Example:
git checkout -b feature/REQ-ADMIN-2-enable-disable-account
```

### 3. Development

#### Setup Environment
```bash
cd aesp-backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

#### Run Tests Locally
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_requirements.py -v

# Run specific test
pytest tests/unit/test_requirements.py::TestAdminRequirements::test_admin_enable_disable_account -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### 4. Implementation Checklist

- [ ] **Code Implementation**
  - [ ] Implement endpoint in `app/routers/xxx.py`
  - [ ] Add models if needed in `app/models/xxx.py`
  - [ ] Add schemas in `app/schemas/xxx.py`
  - [ ] Follow clean code principles

- [ ] **Tests**
  - [ ] Test passes (was SKIPPED, now PASSED)
  - [ ] Add edge case tests
  - [ ] Test error handling
  - [ ] Test authentication/authorization

- [ ] **Documentation**
  - [ ] Add docstrings
  - [ ] Update API docs if needed
  - [ ] Add comments for complex logic

- [ ] **Code Quality**
  - [ ] No print() statements (use logging)
  - [ ] Use timezone-aware datetime
  - [ ] Proper error handling
  - [ ] Follow existing code patterns

### 5. Commit & Push

```bash
# Stage changes
git add .

# Commit with meaningful message
git commit -m "feat(admin): implement enable/disable account toggle

- Add PUT /admin/users/{id}/toggle-status endpoint
- Add admin authorization check
- Update test_admin_enable_disable_account to PASS
- Closes #XX"

# Push to GitHub
git push origin feature/REQ-XXX-feature-name
```

### 6. Create Pull Request

1. Vào GitHub repository
2. Click "New Pull Request"
3. Base: `main` ← Compare: `feature/REQ-XXX-feature-name`
4. Fill in PR template:

```markdown
## 📋 Changes

Implement REQ-ADMIN-2: Enable/Disable Account Toggle

## ✅ Checklist

- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## 🧪 Test Results

- `test_admin_enable_disable_account`: ✅ PASSED (was SKIPPED)

## 📸 Screenshots

<!-- If applicable -->

Closes #XX
```

5. Request review từ team members
6. Chờ approval (cần ít nhất 1 approval)

### 7. After Merge

```bash
# Switch back to main
git checkout main

# Pull latest changes
git pull origin main

# Delete feature branch
git branch -d feature/REQ-XXX-feature-name
```

---

## 🎯 Priority Tasks

### 🔴 HIGH Priority (Làm trước)

1. **REQ-ADMIN-2**: Enable/Disable Account Toggle
2. **REQ-LEARNER-7**: Personalized Learning Path
3. **REQ-LEARNER-8**: Peer Practice Matching
4. **REQ-MENTOR-2**: Assessment Organization
5. **REQ-MENTOR-4**: Mentor Booking System

### 🟡 MEDIUM Priority

6. Admin Mentor List Management
7. Support Ticket System
8. Analytics Dashboard
9. Progress Tracking
10. Vocabulary System

---

## 📝 Code Style

### Python (Backend)

```python
# ✅ GOOD
from datetime import datetime, timezone

@router.post("/example")
async def create_example(
    data: ExampleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new example.
    
    Args:
        data: Example creation data
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Created example object
    """
    example = Example(
        **data.dict(),
        created_at=datetime.now(timezone.utc)
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    
    logger.info(f"Example created: {example.id}")
    return example

# ❌ BAD
@router.post("/example")
def create_example(data):
    print("Creating example")  # Don't use print()
    example = Example(**data)
    example.created_at = datetime.utcnow()  # Deprecated
    db.add(example)
    db.commit()
    return example
```

### Tests

```python
# ✅ GOOD
def test_create_example(client: TestClient, auth_headers: dict):
    """Test creating example with valid data"""
    response = client.post(
        "/examples",
        headers=auth_headers,
        json={"name": "Test Example"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Example"
    assert "id" in data

# ❌ BAD
def test_create_example():
    response = client.post("/examples", json={"name": "Test"})
    assert response.status_code == 201
```

---

## 🆘 Need Help?

- **Slack/Discord**: #aesp-backend channel
- **GitHub Discussions**: Ask questions
- **Code Review**: Tag @team-lead for urgent reviews

---

## 📚 Resources

- [Requirements](./yeucaudetai.txt)
- [Pending Features](./docs/pending_features.md)
- [Test Report](./docs/test_report.md)
- [API Documentation](http://localhost:8000/docs)
