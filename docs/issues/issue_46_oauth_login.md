# Issue #46: OAuth/Social Login (Google)

## 📋 Description
Implement OAuth 2.0 authentication with Google for streamlined user login.

## 🎯 Requirements
- **REQ-AUTH-3**: OAuth authentication with social providers
- Google OAuth 2.0 integration
- Create new user or link to existing user
- Retrieve profile info (email, name, avatar)

## 📌 Acceptance Criteria
- [ ] `GET /auth/google/login` - Initiate Google OAuth flow
- [ ] `GET /auth/google/callback` - Handle OAuth callback
- [ ] `POST /auth/google/token` - Exchange token for JWT
- [ ] `POST /auth/google/link` - Link Google to existing account
- [ ] `DELETE /auth/google/unlink` - Unlink Google from account
- [ ] User created with `auth_provider = 'GOOGLE'`
- [ ] CSRF protection with state parameter

## 🔧 Technical Details
```python
# OAuth Login Flow
GET /auth/google/login
→ Redirect to Google OAuth consent page

# OAuth Callback
GET /auth/google/callback?code=xxx&state=yyy
→ Exchange code for tokens
→ Create/link user
→ Return JWT

# Token Exchange (for mobile apps)
POST /auth/google/token
{
    "access_token": "google_access_token",
    "id_token": "google_id_token"
}

# Response
{
    "access_token": "jwt_token",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "email": "user@gmail.com",
        "full_name": "User Name",
        "avatar_url": "https://..."
    }
}
```

## 📦 Dependencies
- `authlib` or `python-social-auth`
- Google Cloud Console OAuth credentials

## 🔒 Security
- Validate `state` parameter (CSRF)
- Validate `nonce` in ID token
- Verify email is verified in Google

## 🧪 Tests
Tests are prepared in: `tests/unit/test_issue_46_oauth_login.py`

## 📊 Priority
🟢 **Nice to Have** - Improves UX for registration

## 🏷️ Labels
`enhancement`, `backend`, `auth`, `priority-medium`
