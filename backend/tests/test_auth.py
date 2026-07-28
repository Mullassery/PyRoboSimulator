"""Tests for authentication and token management."""

import pytest
from src.services.auth import AuthService


class TestAuthService:
    """Authentication service tests."""

    def test_hash_password(self) -> None:
        """Test password hashing."""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self) -> None:
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed)

    def test_verify_password_incorrect(self) -> None:
        """Test password verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)

        assert not AuthService.verify_password(wrong_password, hashed)

    def test_create_access_token(self) -> None:
        """Test JWT token creation."""
        user_id = 123
        token = AuthService.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self) -> None:
        """Test decoding valid token."""
        user_id = 456
        token = AuthService.create_access_token(user_id)

        decoded_id = AuthService.decode_token(token)

        assert decoded_id == user_id

    def test_decode_token_invalid(self) -> None:
        """Test decoding invalid token."""
        invalid_token = "not.a.valid.token"

        decoded_id = AuthService.decode_token(invalid_token)

        assert decoded_id is None

    def test_decode_token_tampered(self) -> None:
        """Test decoding tampered token."""
        user_id = 789
        token = AuthService.create_access_token(user_id)

        # Tamper with token
        tampered = token[:-5] + "xxxxx"

        decoded_id = AuthService.decode_token(tampered)

        assert decoded_id is None

    def test_password_hashing_consistency(self) -> None:
        """Test that hashing same password produces different hashes."""
        password = "test_password"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)
