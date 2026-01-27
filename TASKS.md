# 📋 AESP Backend - Team Tasks

> **Last Updated:** 2026-01-27
> **Total Tasks:** 19 (15 pending + 4 fixes)
> **Team Members:** Assign yourself to tasks

---

## 🔴 HIGH Priority (5 tasks) - LÀMTRƯỚC

### Task 1: Enable/Disable Account Toggle
- **ID:** REQ-ADMIN-2
- **Assignee:** _Unassigned_
- **Estimated:** 2 hours
- **Status:** 🟡 Todo
- **Test:** `test_admin_enable_disable_account` (SKIPPED → PASSED)

**Implementation:**
- File: `app/routers/admin.py`
- Endpoint: `PUT /admin/users/{user_id}/toggle-status`
- Requirements: Admin authorization, update `is_active` field

**Acceptance Criteria:**
- [ ] Endpoint implemented
- [ ] Admin can toggle user status
- [ ] Test passes
- [ ] Returns proper error for non-existent user

---

### Task 2: Personalized Learning Path
- **ID:** REQ-LEARNER-7
- **Assignee:** _Unassigned_
- **Estimated:** 4 hours
- **Status:** 🟡 Todo
- **Test:** `test_learner_learning_path` (SKIPPED → PASSED)

**Implementation:**
- File: `app/routers/proficiency.py`
- Endpoint: `GET /proficiency/path`
- Requirements: Get user level, recommend topics

**Acceptance Criteria:**
- [ ] Returns current level
- [ ] Returns recommended topics based on level
- [ ] Returns next milestone
- [ ] Test passes

---

### Task 3: Peer Practice Matching
- **ID:** REQ-LEARNER-8
- **Assignee:** _Unassigned_
- **Estimated:** 6 hours
- **Status:** 🟡 Todo
- **Test:** `test_learner_peer_practice` (SKIPPED → PASSED)

**Implementation:**
- File: `app/routers/peer.py`
- Endpoint: `POST /peer/find-partner`
- Requirements: Match by level, create session

**Acceptance Criteria:**
- [ ] Match learners by proficiency level
- [ ] Create practice session
- [ ] Return partner info
- [ ] Test passes

---

### Task 4: Assessment Organization
- **ID:** REQ-MENTOR-2
- **Assignee:** _Unassigned_
- **Estimated:** 5 hours
- **Status:** 🟡 Todo
- **Test:** `test_mentor_access_assessments` (SKIPPED → PASSED)

**Implementation:**
- File: `app/routers/mentor.py`
- Endpoint: `GET /mentor-sessions`
- Requirements: List mentor's sessions, schedule assessments

**Acceptance Criteria:**
- [ ] Mentor can view sessions
- [ ] Can schedule new assessments
- [ ] Can assign proficiency levels
- [ ] Test passes

---

### Task 5: Mentor Booking System
- **ID:** REQ-MENTOR-BOOKING
- **Assignee:** _Unassigned_
- **Estimated:** 4 hours
- **Status:** 🟡 Todo
- **Test:** Multiple tests in `test_mentor.py`

**Implementation:**
- File: `app/routers/mentor.py`
- Endpoints: `POST /mentors/availability`, `GET /mentors/bookings`
- Requirements: Set schedule, accept/reject bookings

**Acceptance Criteria:**
- [ ] Mentor can set availability
- [ ] Learner can book sessions
- [ ] Mentor can accept/reject
- [ ] Tests pass

---

## 🟡 MEDIUM Priority (6 tasks)

### Task 6: Manage Mentor List
- **ID:** REQ-ADMIN-5
- **Assignee:** _Unassigned_
- **Estimated:** 3 hours
- **Status:** 🟡 Todo

**Implementation:**
- File: `app/routers/admin.py`
- Endpoint: `GET /admin/mentors`

---

### Task 7: Support Ticket System
- **ID:** REQ-ADMIN-8
- **Assignee:** _Unassigned_
- **Estimated:** 5 hours
- **Status:** 🟡 Todo

**Implementation:**
- File: `app/routers/support.py`
- Endpoints: `GET /support/tickets`, `POST /support/tickets`, `PUT /support/tickets/{id}`

---

### Task 8: Admin Statistics Dashboard
- **ID:** REQ-ADMIN-13
- **Assignee:** _Unassigned_
- **Estimated:** 4 hours
- **Status:** 🟡 Todo

**Implementation:**
- File: `app/routers/analytics.py`
- Endpoint: `GET /analytics/admin/summary`

---

### Task 9: Progress Analytics
- **ID:** REQ-LEARNER-11
- **Assignee:** _Unassigned_
- **Estimated:** 4 hours
- **Status:** 🟡 Todo

**Implementation:**
- File: `app/routers/analytics.py`
- Endpoint: `GET /analytics/learner/progress`

---

### Task 10: Vocabulary System
- **ID:** REQ-LEARNER-10 / REQ-MENTOR-8
- **Assignee:** _Unassigned_
- **Estimated:** 5 hours
- **Status:** 🟡 Todo

**Implementation:**
- File: `app/routers/vocab.py`
- Endpoints: `GET /vocab`, `POST /vocab/save`

---

### Task 11: Mentor Resources
- **ID:** REQ-MENTOR-3
- **Assignee:** _Unassigned_
- **Estimated:** 3 hours
- **Status:** 🟡 Todo

**Implementation:**
- File: `app/routers/mentor.py`
- Endpoint: `GET /mentors/resources`

---

## 🟢 LOW Priority (4 tasks)

### Task 12: Purchase History Export
- **ID:** REQ-ADMIN-11
- **Assignee:** _Unassigned_
- **Estimated:** 2 hours

### Task 13: Weekly/Monthly Reports
- **ID:** REQ-LEARNER-14
- **Assignee:** _Unassigned_
- **Estimated:** 3 hours

### Task 14: Daily Stats
- **Assignee:** _Unassigned_
- **Estimated:** 2 hours

### Task 15: Achievements System
- **Assignee:** _Unassigned_
- **Estimated:** 4 hours

---

## ⚠️ Bug Fixes (4 tasks)

### Fix 1: Content Creation Routes
- **Status:** 🔴 Failed Test
- **Assignee:** _Unassigned_
- **Estimated:** 1 hour
- **Tests:** `test_create_topic`, `test_create_scenario`

**Issue:** Route structure mismatch
**Fix:** Verify endpoint paths in `app/routers/content.py`

---

### Fix 2: Subscription Upgrade
- **Status:** 🔴 Failed Test
- **Assignee:** _Unassigned_
- **Estimated:** 2 hours
- **Test:** `test_upgrade_subscription`

**Issue:** Endpoint not fully implemented
**Fix:** Complete logic in `app/routers/payment.py`

---

### Fix 3: Subscription Cancel
- **Status:** 🔴 Failed Test
- **Assignee:** _Unassigned_
- **Estimated:** 1 hour
- **Test:** `test_cancel_subscription`

**Issue:** Endpoint not fully implemented
**Fix:** Complete logic in `app/routers/payment.py`

---

### Fix 4: Delete Topic Admin Check
- **Status:** 🔴 Failed Test
- **Assignee:** _Unassigned_
- **Estimated:** 0.5 hour
- **Test:** `test_delete_topic`

**Issue:** Missing admin authorization
**Fix:** Add `require_admin()` dependency

---

## 📊 Progress Tracking

| Priority | Total | Completed | In Progress | Todo |
|----------|-------|-----------|-------------|------|
| 🔴 HIGH | 5 | 0 | 0 | 5 |
| 🟡 MEDIUM | 6 | 0 | 0 | 6 |
| 🟢 LOW | 4 | 0 | 0 | 4 |
| ⚠️ FIXES | 4 | 0 | 0 | 4 |
| **TOTAL** | **19** | **0** | **0** | **19** |

---

## 🎯 Sprint Planning

### Sprint 1 (Week 1)
- [ ] Task 1: Enable/Disable Account
- [ ] Task 4: Assessment Organization
- [ ] Fix 1-4: All bug fixes

### Sprint 2 (Week 2)
- [ ] Task 2: Learning Path
- [ ] Task 3: Peer Matching
- [ ] Task 5: Booking System

### Sprint 3 (Week 3)
- [ ] Task 6-11: MEDIUM priority features

### Sprint 4 (Week 4)
- [ ] Task 12-15: LOW priority features
- [ ] Final testing & documentation

---

## 📝 How to Claim a Task

1. Comment trên GitHub Issue: "I'll take this"
2. Assign issue cho mình
3. Update status trong file này
4. Create branch: `feature/REQ-XXX-task-name`
5. Start coding!

---

**📌 Note:** Update file này khi claim task hoặc complete task để team biết progress!
