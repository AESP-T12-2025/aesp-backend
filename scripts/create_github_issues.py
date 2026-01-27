"""
Script to automatically create GitHub issues from TASKS.md
Usage: python scripts/create_github_issues.py
Requires: pip install PyGithub
"""
import os
from github import Github

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set this in environment
REPO_NAME = "AESP-T12-2025/aesp-backend"

# Tasks definition
TASKS = [
    # HIGH PRIORITY
    {
        "title": "[HIGH] REQ-ADMIN-2: Enable/Disable Account Toggle",
        "body": """## 📋 Feature Information

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

## 🧪 Test Coverage

**Test file:** `tests/unit/test_requirements.py`
**Test function:** `test_admin_enable_disable_account`

## 📚 Related

- Requirements: yeucaudetai.txt line 23
- Pending features: docs/pending_features.md
""",
        "labels": ["enhancement", "high-priority", "admin"]
    },
    {
        "title": "[HIGH] REQ-LEARNER-7: Personalized Learning Path",
        "body": """## 📋 Feature Information

**Feature ID:** REQ-LEARNER-7
**Priority:** 🔴 HIGH
**Role:** Learner
**Estimated Time:** 4 hours

## 📝 Description

Implement adaptive learning path based on user's proficiency level.

## ✅ Acceptance Criteria

- [ ] Endpoint `GET /proficiency/path` implemented
- [ ] Returns current level
- [ ] Returns recommended topics
- [ ] Returns next milestone
- [ ] Test passes

## 🔧 Implementation Details

**File:** `app/routers/proficiency.py`
**Endpoint:** `GET /proficiency/path`

## 🧪 Test Coverage

**Test file:** `tests/unit/test_requirements.py`
**Test function:** `test_learner_learning_path`
""",
        "labels": ["enhancement", "high-priority", "learner"]
    },
    {
        "title": "[HIGH] REQ-LEARNER-8: Peer Practice Matching",
        "body": """## 📋 Feature Information

**Feature ID:** REQ-LEARNER-8
**Priority:** 🔴 HIGH
**Role:** Learner
**Estimated Time:** 6 hours

## 📝 Description

Implement peer matching system for learners to practice together.

## ✅ Acceptance Criteria

- [ ] Match learners by proficiency level
- [ ] Create practice session
- [ ] Return partner information
- [ ] Test passes

## 🔧 Implementation Details

**File:** `app/routers/peer.py`
**Endpoint:** `POST /peer/find-partner`
""",
        "labels": ["enhancement", "high-priority", "learner"]
    },
    {
        "title": "[HIGH] REQ-MENTOR-2: Assessment Organization",
        "body": """## 📋 Feature Information

**Feature ID:** REQ-MENTOR-2
**Priority:** 🔴 HIGH
**Role:** Mentor
**Estimated Time:** 5 hours

## 📝 Description

Mentor can organize and conduct assessments for learners.

## ✅ Acceptance Criteria

- [ ] Mentor can view sessions
- [ ] Can schedule assessments
- [ ] Can assign proficiency levels
- [ ] Test passes
""",
        "labels": ["enhancement", "high-priority", "mentor"]
    },
    {
        "title": "[HIGH] Mentor Booking System",
        "body": """## 📋 Feature Information

**Priority:** 🔴 HIGH
**Role:** Mentor/Learner
**Estimated Time:** 4 hours

## 📝 Description

Complete mentor booking system for learners to schedule sessions.

## ✅ Acceptance Criteria

- [ ] Mentor can set availability
- [ ] Learner can book sessions
- [ ] Mentor can accept/reject bookings
- [ ] Tests pass
""",
        "labels": ["enhancement", "high-priority", "mentor"]
    },
    
    # BUG FIXES
    {
        "title": "[BUG] Content Creation Routes - Test Failed",
        "body": """## 🐛 Bug Description

Tests `test_create_topic` and `test_create_scenario` are failing.

## 🔍 Issue

Route structure mismatch between tests and implementation.

## ✅ Expected

Tests should pass.

## 🔧 Fix Needed

Verify endpoint paths in `app/routers/content.py` match test expectations.
""",
        "labels": ["bug", "high-priority"]
    },
    {
        "title": "[BUG] Subscription Upgrade - Test Failed",
        "body": """## 🐛 Bug Description

Test `test_upgrade_subscription` is failing.

## 🔍 Issue

Endpoint not fully implemented.

## 🔧 Fix Needed

Complete logic in `app/routers/payment.py` for subscription upgrades.
""",
        "labels": ["bug", "medium-priority", "payment"]
    },
]


def create_issues():
    """Create GitHub issues from TASKS list"""
    if not GITHUB_TOKEN:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("Set it with: export GITHUB_TOKEN=your_token_here")
        return
    
    # Initialize GitHub client
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    print(f"📋 Creating {len(TASKS)} issues in {REPO_NAME}...")
    
    created = 0
    for task in TASKS:
        try:
            issue = repo.create_issue(
                title=task["title"],
                body=task["body"],
                labels=task["labels"]
            )
            print(f"✅ Created: #{issue.number} - {task['title']}")
            created += 1
        except Exception as e:
            print(f"❌ Failed to create: {task['title']}")
            print(f"   Error: {e}")
    
    print(f"\n🎉 Done! Created {created}/{len(TASKS)} issues")
    print(f"View at: https://github.com/{REPO_NAME}/issues")


if __name__ == "__main__":
    create_issues()
