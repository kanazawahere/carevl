"""
Test Authentication Flow - Invite Code Authentication

Tests the complete authentication flow:
1. Invite code validation
2. PAT storage in Credential Manager
3. Git operations (clone/pull)
4. PIN setup and verification
5. Database initialization/restore
"""

import pytest
import base64
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.services.invite_code import InviteCodeService, InviteCodeData
from app.services.credential_manager import CredentialManager
from app.services.git_operations import GitOperations


class TestInviteCodeValidation:
    """Test invite code encoding/decoding"""
    
    def test_encode_decode_basic(self):
        """Test basic encode and decode"""
        data = {
            "station_id": "TRAM_001",
            "station_name": "Trạm Y Tế Xã A",
            "repo_url": "https://github.com/bot/station-001",
            "pat": "ghp_test123456789"
        }
        
        code = InviteCodeService.encode(data)
        decoded = InviteCodeService.decode(code)
        
        assert decoded.station_id == data["station_id"]
        assert decoded.station_name == data["station_name"]
        assert decoded.repo_url == data["repo_url"]
        assert decoded.pat == data["pat"]
        assert decoded.encryption_key is None
    
    def test_encode_decode_with_encryption_key(self):
        """Test encode/decode with encryption key"""
        data = {
            "station_id": "TRAM_002",
            "station_name": "Trạm Y Tế Xã B",
            "repo_url": "https://github.com/bot/station-002",
            "pat": "ghp_test987654321",
            "encryption_key": "my-32-byte-encryption-key-here"
        }
        
        code = InviteCodeService.encode(data)
        decoded = InviteCodeService.decode(code)
        
        assert decoded.encryption_key == data["encryption_key"]
    
    def test_validate_valid_code(self):
        """Test validation of valid invite code"""
        data = {
            "station_id": "TRAM_003",
            "station_name": "Test Station",
            "repo_url": "https://github.com/bot/station-003",
            "pat": "ghp_validtoken"
        }
        
        code = InviteCodeService.encode(data)
        is_valid, error = InviteCodeService.validate(code)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_base64(self):
        """Test validation of invalid base64"""
        is_valid, error = InviteCodeService.validate("not-valid-base64!!!")
        
        assert is_valid is False
        assert "Invalid Base64" in error or "base64" in error.lower()
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields"""
        # Create JSON without required fields
        incomplete_data = {
            "station_id": "TRAM_004"
            # Missing station_name, repo_url, pat
        }
        
        code = base64.urlsafe_b64encode(
            json.dumps(incomplete_data).encode()
        ).decode()
        
        is_valid, error = InviteCodeService.validate(code)
        
        assert is_valid is False
        assert "Missing or invalid fields" in error or "Field required" in error
    
    def test_validate_invalid_json(self):
        """Test validation of invalid JSON"""
        code = base64.urlsafe_b64encode(b"not json").decode()
        is_valid, error = InviteCodeService.validate(code)
        
        assert is_valid is False
        assert "Invalid JSON" in error


class TestCredentialManager:
    """Test credential storage and retrieval"""
    
    @patch('keyring.set_password')
    @patch('keyring.get_password')
    def test_save_and_get_pat(self, mock_get, mock_set):
        """Test saving and retrieving PAT"""
        station_id = "TRAM_005"
        pat = "ghp_test_token_12345"
        
        # Mock keyring
        mock_set.return_value = None
        mock_get.return_value = pat
        
        # Save PAT
        result = CredentialManager.save_pat(station_id, pat)
        assert result is True
        
        # Retrieve PAT
        retrieved = CredentialManager.get_pat(station_id)
        assert retrieved == pat
    
    @patch('keyring.set_password')
    @patch('keyring.get_password')
    def test_save_and_get_encryption_key(self, mock_get, mock_set):
        """Test saving and retrieving encryption key"""
        station_id = "TRAM_006"
        key = "my-encryption-key-32-bytes-long"
        
        # Mock keyring
        mock_set.return_value = None
        mock_get.return_value = key
        
        # Save key
        result = CredentialManager.save_encryption_key(station_id, key)
        assert result is True
        
        # Retrieve key
        retrieved = CredentialManager.get_encryption_key(station_id)
        assert retrieved == key
    
    @patch('keyring.get_password')
    def test_get_nonexistent_pat(self, mock_get):
        """Test retrieving non-existent PAT"""
        mock_get.return_value = None
        
        pat = CredentialManager.get_pat("NONEXISTENT")
        assert pat is None


class TestGitOperations:
    """Test Git operations"""
    
    @patch('subprocess.run')
    def test_check_git_installed(self, mock_run):
        """Test checking if Git is installed"""
        mock_run.return_value = Mock(returncode=0)
        
        result = GitOperations.check_git_installed()
        assert result is True
    
    @patch('subprocess.run')
    def test_check_git_not_installed(self, mock_run):
        """Test when Git is not installed"""
        mock_run.side_effect = FileNotFoundError()
        
        result = GitOperations.check_git_installed()
        assert result is False
    
    @patch('subprocess.run')
    def test_clone_repo_success(self, mock_run):
        """Test successful repository clone"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        repo_url = "https://github.com/bot/station-001"
        pat = "ghp_test_token"
        repo_dir = Path("./test_repo")
        
        success, message = GitOperations.clone_repo(repo_url, pat, repo_dir)
        
        assert success is True
        assert "successfully" in message.lower()
    
    @patch('subprocess.run')
    def test_clone_repo_failure(self, mock_run):
        """Test failed repository clone"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="fatal: repository not found"
        )
        
        repo_url = "https://github.com/bot/nonexistent"
        pat = "ghp_test_token"
        repo_dir = Path("./test_repo")
        
        success, message = GitOperations.clone_repo(repo_url, pat, repo_dir)
        
        assert success is False
        assert "failed" in message.lower()


class TestPINSetup:
    """Test PIN setup and verification"""
    
    def test_pin_encryption_decryption(self):
        """Test PIN-based encryption and decryption"""
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import os
        
        pin = "123456"
        token = "ghp_test_token_12345"
        salt = os.urandom(16)
        
        # Encrypt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
        f = Fernet(key)
        encrypted = f.encrypt(token.encode())
        
        # Decrypt
        kdf2 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key2 = base64.urlsafe_b64encode(kdf2.derive(pin.encode()))
        f2 = Fernet(key2)
        decrypted = f2.decrypt(encrypted).decode()
        
        assert decrypted == token
    
    def test_wrong_pin_fails_decryption(self):
        """Test that wrong PIN fails to decrypt"""
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import os
        
        correct_pin = "123456"
        wrong_pin = "654321"
        token = "ghp_test_token_12345"
        salt = os.urandom(16)
        
        # Encrypt with correct PIN
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(correct_pin.encode()))
        f = Fernet(key)
        encrypted = f.encrypt(token.encode())
        
        # Try to decrypt with wrong PIN
        kdf2 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key2 = base64.urlsafe_b64encode(kdf2.derive(wrong_pin.encode()))
        f2 = Fernet(key2)
        
        with pytest.raises(InvalidToken):
            f2.decrypt(encrypted)


class TestEndToEndFlow:
    """Test complete authentication flow"""
    
    @patch('app.services.git_operations.GitOperations.check_git_installed')
    @patch('app.services.git_operations.GitOperations.clone_repo')
    @patch('app.services.credential_manager.CredentialManager.save_pat')
    @patch('app.services.credential_manager.CredentialManager.save_encryption_key')
    def test_complete_new_station_setup(
        self,
        mock_save_key,
        mock_save_pat,
        mock_clone,
        mock_git_check
    ):
        """Test complete flow for new station setup"""
        # Setup mocks
        mock_git_check.return_value = True
        mock_save_pat.return_value = True
        mock_save_key.return_value = True
        mock_clone.return_value = (True, "Clone successful")
        
        # 1. Create invite code
        data = {
            "station_id": "TRAM_TEST_01",
            "station_name": "Trạm Test",
            "repo_url": "https://github.com/bot/station-test-01",
            "pat": "ghp_test_token_complete",
            "encryption_key": "test-encryption-key-32-bytes"
        }
        
        invite_code = InviteCodeService.encode(data)
        
        # 2. Validate invite code
        is_valid, error = InviteCodeService.validate(invite_code)
        assert is_valid is True
        
        # 3. Decode invite code
        decoded = InviteCodeService.decode(invite_code)
        assert decoded.station_id == data["station_id"]
        
        # 4. Check Git installed
        assert GitOperations.check_git_installed() is True
        
        # 5. Save PAT
        assert CredentialManager.save_pat(decoded.station_id, decoded.pat) is True
        
        # 6. Save encryption key
        assert CredentialManager.save_encryption_key(
            decoded.station_id,
            decoded.encryption_key
        ) is True
        
        # 7. Clone repository
        repo_dir = Path(f"./data/repos/{decoded.station_id}")
        success, message = GitOperations.clone_repo(
            decoded.repo_url,
            decoded.pat,
            repo_dir
        )
        assert success is True
        
        # 8. Setup PIN (tested separately)
        # 9. Initialize database (tested separately)
        
        print("✅ Complete new station setup flow passed")
    
    @patch('app.services.git_operations.GitOperations.check_git_installed')
    @patch('app.services.git_operations.GitOperations.clone_repo')
    @patch('app.services.credential_manager.CredentialManager.save_pat')
    def test_complete_restore_station_setup(
        self,
        mock_save_pat,
        mock_clone,
        mock_git_check
    ):
        """Test complete flow for restoring existing station"""
        # Setup mocks
        mock_git_check.return_value = True
        mock_save_pat.return_value = True
        mock_clone.return_value = (True, "Clone successful")
        
        # 1. Create invite code (same as new setup)
        data = {
            "station_id": "TRAM_RESTORE_01",
            "station_name": "Trạm Restore",
            "repo_url": "https://github.com/bot/station-restore-01",
            "pat": "ghp_restore_token"
        }
        
        invite_code = InviteCodeService.encode(data)
        
        # 2. Validate and decode
        is_valid, _ = InviteCodeService.validate(invite_code)
        assert is_valid is True
        
        decoded = InviteCodeService.decode(invite_code)
        
        # 3. Save credentials
        assert CredentialManager.save_pat(decoded.station_id, decoded.pat) is True
        
        # 4. Clone repository
        success, _ = GitOperations.clone_repo(
            decoded.repo_url,
            decoded.pat,
            Path(f"./data/repos/{decoded.station_id}")
        )
        assert success is True
        
        # 5. Find and restore snapshot (tested separately)
        # 6. Setup PIN (tested separately)
        
        print("✅ Complete restore station setup flow passed")


class TestGithubReleasesHelpers:
    def test_parse_owner_repo(self):
        from app.services.github_releases import parse_owner_repo

        assert parse_owner_repo("https://github.com/org/foo") == ("org", "foo")
        assert parse_owner_repo("https://github.com/org/foo.git") == ("org", "foo")

    def test_find_latest_db_enc_prefers_final(self):
        from app.services.github_releases import find_latest_db_enc_asset

        assets = [
            {"name": "readme.txt", "browser_download_url": "https://x/r"},
            {"name": "old.db.enc", "browser_download_url": "https://x/old"},
            {"name": "FINAL_SITE_2026.db.enc", "browser_download_url": "https://x/final"},
        ]
        url, name = find_latest_db_enc_asset(assets)
        assert name == "FINAL_SITE_2026.db.enc"
        assert "final" in url


class TestBrowserSession:
    def test_session_value_roundtrip(self):
        from app.services.browser_session import issue_session_value, verify_session_value

        v = issue_session_value()
        assert verify_session_value(v) is True
        assert verify_session_value("bad") is False


class TestChangePinRewrap:
    def test_change_pin_rewrap(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401 — register metadata
        from app.core.database import Base
        from app.services.pin_change import assert_pin_change_allowed, change_pin_rewrap
        from app.services.pin_vault import save_pin_with_secret

        eng = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(eng)
        S = sessionmaker(bind=eng)
        db = S()
        save_pin_with_secret(db, "111111", "secret-token")
        db.commit()
        assert_pin_change_allowed(db)
        ok, err = change_pin_rewrap(db, "111111", "222222")
        assert ok is True and err == ""
        db.commit()
        ok2, err2 = change_pin_rewrap(db, "333333", "444444")
        assert ok2 is False and err2 == "invalid_old_pin"


class TestCryptoInviteKey:
    def test_aes_key_utf8_32(self):
        from app.services.crypto import aes_key_from_invite_field

        raw = "x" * 32
        assert len(aes_key_from_invite_field(raw)) == 32


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
