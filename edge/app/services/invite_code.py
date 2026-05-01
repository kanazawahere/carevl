"""Invite code service for station provisioning"""

import base64
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError


class InviteCodeData(BaseModel):
    """Invite code structure"""
    station_id: str = Field(..., min_length=1, max_length=100)
    station_name: str = Field(..., min_length=1, max_length=255)
    repo_url: str = Field(..., pattern=r"^https://github\.com/.+/.+$")
    pat: Optional[str] = Field(None, min_length=10)          # Classic PAT (legacy git)
    ssh_private_key: Optional[str] = None                    # SSH deploy key (git clone/push)
    encryption_key: Optional[str] = None

    @property
    def auth_type(self) -> str:
        return "ssh" if self.ssh_private_key else "pat"

    def model_post_init(self, __context: Any) -> None:
        if not self.pat and not self.ssh_private_key:
            raise ValueError("Invite code must contain either 'pat' or 'ssh_private_key'")


class InviteCodeService:
    """Service for handling invite code operations"""
    
    @staticmethod
    def encode(data: Dict[str, Any]) -> str:
        """
        Encode invite code data to Base64 string
        
        Args:
            data: Dictionary with station_id, station_name, repo_url, pat
        
        Returns:
            Base64 encoded string
        
        Example:
            >>> data = {
            ...     "station_id": "station-001",
            ...     "station_name": "Tram Y Te Xa A",
            ...     "repo_url": "https://github.com/org/station-001",
            ...     "pat": "ghp_xxxxxxxxxxxx"
            ... }
            >>> code = InviteCodeService.encode(data)
        """
        # Validate data
        InviteCodeData(**data)
        
        # Convert to JSON
        json_str = json.dumps(data, ensure_ascii=False)
        
        # Encode to Base64
        encoded = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        return encoded
    
    @staticmethod
    def decode(invite_code: str) -> InviteCodeData:
        """
        Decode and validate invite code
        
        Args:
            invite_code: Base64 encoded string
        
        Returns:
            InviteCodeData object
        
        Raises:
            ValueError: If code is invalid or malformed
            ValidationError: If required fields are missing
        
        Example:
            >>> code = "eyJzdGF0aW9uX2lkIjogInN0YXRpb24tMDAxIn0="
            >>> data = InviteCodeService.decode(code)
            >>> print(data.station_id)
            station-001
        """
        try:
            # Decode from Base64
            decoded_bytes = base64.urlsafe_b64decode(invite_code.encode('utf-8'))
            json_str = decoded_bytes.decode('utf-8')
            
            # Parse JSON
            data_dict = json.loads(json_str)
            
            # Validate with Pydantic
            data = InviteCodeData(**data_dict)
            
            return data
            
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid Base64 encoding: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except ValidationError as e:
            raise ValueError(f"Missing or invalid fields: {e}")
    
    @staticmethod
    def validate(invite_code: str) -> tuple[bool, Optional[str]]:
        """
        Validate invite code without raising exceptions
        
        Args:
            invite_code: Base64 encoded string
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Example:
            >>> is_valid, error = InviteCodeService.validate(code)
            >>> if not is_valid:
            ...     print(f"Error: {error}")
        """
        try:
            InviteCodeService.decode(invite_code)
            return True, None
        except ValueError as e:
            return False, str(e)
