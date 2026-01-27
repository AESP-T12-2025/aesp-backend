# 🚀 Setup GitHub cho Team AESP

## Bước 1: Tạo GitHub Issues từ Tasks

### Tự động tạo issues (Recommended)

```bash
# Clone repo
git clone https://github.com/AESP-T12-2025/aesp-backend.git
cd aesp-backend

# Chạy script tạo issues (sẽ tạo sau)
python scripts/create_github_issues.py
```

### Hoặc tạo thủ công

Vào https://github.com/AESP-T12-2025/aesp-backend/issues/new

**Ví dụ Issue #1:**
```markdown
Title: [HIGH] REQ-ADMIN-2: Enable/Disable Account Toggle

Labels: enhancement, high-priority, admin

Body:
## 📋 Feature Information

**Feature ID:** REQ-ADMIN-2
**Priority:** 🔴 HIGH
**Role:** Admin
**Estimated Time:** 2 hours

## 📝 Description

Implement endpoint để Admin có thể enable/disable user accounts.

## ✅ Acceptance Criteria

- [ ] Endpoint `PUT /admin/users/{user_id}/toggle-status` implemented
- [ ] Admin authorization check
- [ ] Test `test_admin_enable_disable_account` passes (SKIPPED → PASSED)
- [ ] Returns 404 for non-existent user

## 🔧 Implementation Details

**File:** `app/routers/admin.py`
**Endpoint:** `PUT /admin/users/{user_id}/toggle-status`

**Response:**
```json
{
  "message": "User activated/deactivated"
}
```

## 🧪 Test Coverage

**Test file:** `tests/unit/test_requirements.py`
**Test function:** `test_admin_enable_disable_account`

## 📚 Related

- Requirements: yeucaudetai.txt line 23
- Test report: docs/test_report.md
```

Tạo tương tự cho 19 tasks còn lại.

---

## Bước 2: Setup GitHub Project Board

### 2.1 Tạo Project

1. Vào https://github.com/orgs/AESP-T12-2025/projects
2. Click "New project"
3. Chọn "Board" template
4. Name: "AESP Backend Development"

### 2.2 Tạo Columns

- 📋 **Backlog** (Todo)
- 🏗️ **In Progress**
- 👀 **In Review** (PR created)
- ✅ **Done**

### 2.3 Add Issues to Board

1. Click "Add items"
2. Chọn tất cả issues vừa tạo
3. Drag vào column "Backlog"

### 2.4 Setup Automation

**Settings → Workflows:**
- ✅ Auto-add to project when issue created
- ✅ Move to "In Progress" when issue assigned
- ✅ Move to "In Review" when PR linked
- ✅ Move to "Done" when PR merged

---

## Bước 3: Setup Branch Protection

### 3.1 Protect Main Branch

**Settings → Branches → Add rule:**

Branch name pattern: `main`

Rules:
- ✅ Require pull request before merging
- ✅ Require approvals: 1
- ✅ Require status checks to pass
  - ✅ Backend Tests (from GitHub Actions)
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings

### 3.2 Protect Official Branch

Same rules for `official` branch.

---

## Bước 4: Setup GitHub Actions

Files đã tạo:
- `.github/workflows/test.yml` - Auto run tests on PR

### 4.1 Add Secrets

**Settings → Secrets → Actions:**

```
GEMINI_API_KEY=your_api_key_here
```

### 4.2 Enable Actions

**Settings → Actions → General:**
- ✅ Allow all actions and reusable workflows

---

## Bước 5: Setup Team Members

### 5.1 Invite Members

**Settings → Collaborators:**
- Add team members với role "Write"

### 5.2 Assign Code Owners

Tạo file `.github/CODEOWNERS`:

```
# Backend code owners
/aesp-backend/app/routers/admin.py @team-lead
/aesp-backend/app/routers/payment.py @team-lead
/aesp-backend/tests/ @team-lead

# Auto-request review from these people
* @team-lead @member1
```

---

## Bước 6: Team Workflow

### 6.1 Daily Standup (Optional)

**Format:**
- Yesterday: Task X completed
- Today: Working on Task Y
- Blockers: None / Need help with Z

### 6.2 Code Review Process

**Reviewer checklist:**
- [ ] Code follows style guide
- [ ] Tests pass
- [ ] No console.log/print() statements
- [ ] Proper error handling
- [ ] Documentation updated

**Approval:**
- Cần ít nhất 1 approval để merge
- Team lead review cho critical features

### 6.3 Merge Strategy

**Squash and merge** (recommended):
- Keeps history clean
- One commit per feature

---

## Bước 7: Documentation

### 7.1 Update README

```markdown
# AESP Backend

## Quick Start

```bash
# Clone
git clone https://github.com/AESP-T12-2025/aesp-backend.git

# Setup
cd aesp-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run server
uvicorn app.main:app --reload
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

## Tasks

See [TASKS.md](./TASKS.md)
```

---

## Bước 8: Monitoring & Metrics

### 8.1 GitHub Insights

**Insights → Pulse:**
- Track weekly activity
- PRs merged
- Issues closed

### 8.2 Test Coverage

**After setup Codecov:**
- Badge in README
- Coverage reports on PRs

---

## 📋 Checklist Setup

- [ ] GitHub Issues created (19 issues)
- [ ] Project Board setup
- [ ] Branch protection enabled
- [ ] GitHub Actions working
- [ ] Secrets configured
- [ ] Team members invited
- [ ] CODEOWNERS setup
- [ ] Documentation updated

---

## 🆘 Troubleshooting

### Tests fail on GitHub Actions but pass locally

**Solution:**
```bash
# Check environment variables
# Make sure DATABASE_URL is set in GitHub Secrets
```

### Can't push to main

**Solution:**
- Create PR instead
- Don't push directly to main

### PR blocked by failing tests

**Solution:**
```bash
# Run tests locally first
pytest tests/ -v

# Fix failing tests
# Push again
```

---

## 📚 Resources

- [GitHub Projects Guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub Actions](https://docs.github.com/en/actions)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [TASKS.md](./TASKS.md)
