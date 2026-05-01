"""Windows Credential Manager integration using keyring"""

import keyring
from typing import Optional


class CredentialManager:
    """Manage credentials in Windows Credential Manager"""
    
    SERVICE_NAME = "CareVL"
    
    @staticmethod
    def save_pat(station_id: str, pat: str) -> bool:
        """
        Save GitHub PAT to Windows Credential Manager
        
        Args:
            station_id: Station identifier (used as username)
            pat: GitHub Personal Access Token
        
        Returns:
            True if successful
        
        Example:
            >>> CredentialManager.save_pat("station-001", "ghp_xxxx")
            True
        """
        try:
            keyring.set_password(
                CredentialManager.SERVICE_NAME,
                station_id,
                pat
            )
            return True
        except Exception as e:
            print(f"Failed to save PAT: {e}")
            return False
    
    @staticmethod
    def get_pat(station_id: str) -> Optional[str]:
        """
        Retrieve GitHub PAT from Windows Credential Manager
        
        Args:
            station_id: Station identifier
        
        Returns:
            PAT string or None if not found
        
        Example:
            >>> pat = CredentialManager.get_pat("station-001")
            >>> if pat:
            ...     print("PAT found")
        """
        try:
            pat = keyring.get_password(
                CredentialManager.SERVICE_NAME,
                station_id
            )
            return pat
        except Exception as e:
            print(f"Failed to retrieve PAT: {e}")
            return None
    
    @staticmethod
    def delete_pat(station_id: str) -> bool:
        """
        Delete GitHub PAT from Windows Credential Manager
        
        Args:
            station_id: Station identifier
        
        Returns:
            True if successful
        
        Example:
            >>> CredentialManager.delete_pat("station-001")
            True
        """
        try:
            keyring.delete_password(
                CredentialManager.SERVICE_NAME,
                station_id
            )
            return True
        except Exception as e:
            print(f"Failed to delete PAT: {e}")
            return False
    
    @staticmethod
    def save_encryption_key(station_id: str, key: str) -> bool:
        """
        Save encryption key to Windows Credential Manager
        
        Args:
            station_id: Station identifier
            key: Base64 encryption key
        
        Returns:
            True if successful
        """
        try:
            keyring.set_password(
                f"{CredentialManager.SERVICE_NAME}_ENCRYPTION",
                station_id,
                key
            )
            return True
        except Exception as e:
            print(f"Failed to save encryption key: {e}")
            return False
    
    @staticmethod
    def get_encryption_key(station_id: str) -> Optional[str]:
        """Retrieve encryption key from Windows Credential Manager"""
        try:
            key = keyring.get_password(
                f"{CredentialManager.SERVICE_NAME}_ENCRYPTION",
                station_id
            )
            return key
        except Exception as e:
            print(f"Failed to retrieve encryption key: {e}")
            return None
