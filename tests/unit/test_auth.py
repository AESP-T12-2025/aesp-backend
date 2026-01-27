"""
Unit tests for Authentication endpoints
Tests: registration, login, token validation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestAuthRegistration:
    """Test user registration"""

    def test_register_success(self, client: TestClient, test_user_data: dict):
        """Test successful user registration"""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "password" not in data  # Password should not be returned

    def test_register_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate email fails"""
        # First registration
        client.post("/auth/register", json=test_user_data)
        
        # Second registration with same email
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        # Check for error message (flexible for language)
        detail = response.json()["detail"].lower()
        assert "already registered" in detail or "đã được đăng ký" in detail

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email fails"""
        response = client.post("/auth/register", json={
            "email": "invalid-email",
            "password": "Test123!",
            "full_name": "Test"
        })
        
        assert response.status_code == 422  # Validation error


class TestAuthLogin:
    """Test user login"""

    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Test successful login returns access token"""
        # Register first
        client.post("/auth/register", json=test_user_data)
        
        # Login
        response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user_data: dict):
        """Test login with wrong password fails"""
        # Register first
        client.post("/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user fails"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Test123!"
        })
        
        assert response.status_code == 401


class TestAuthToken:
    """Test token validation"""

    def test_protected_endpoint_with_token(self, client: TestClient, auth_headers: dict):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/users/me", headers=auth_headers)
        
        assert response.status_code == 200

    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token fails"""
        response = client.get("/users/me")
        
        assert response.status_code == 401

    def test_protected_endpoint_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token fails"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
