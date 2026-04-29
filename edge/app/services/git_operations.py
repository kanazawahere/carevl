"""Git operations for station provisioning"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple


class GitOperations:
    """Handle Git operations with PAT authentication"""
    
    @staticmethod
    def clone_repo(repo_url: str, pat: str, target_dir: Path) -> Tuple[bool, str]:
        """
        Clone repository using PAT authentication
        
        Args:
            repo_url: GitHub repository URL (https://github.com/org/repo)
            pat: GitHub Personal Access Token
            target_dir: Target directory for clone
        
        Returns:
            Tuple of (success, message)
        
        Example:
            >>> success, msg = GitOperations.clone_repo(
            ...     "https://github.com/org/station-001",
            ...     "ghp_xxxx",
            ...     Path("./data/repo")
            ... )
        """
        try:
            # Inject PAT into URL
            # https://github.com/org/repo -> https://pat@github.com/org/repo
            auth_url = repo_url.replace("https://", f"https://{pat}@")
            
            # Create target directory
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Clone repository
            result = subprocess.run(
                ["git", "clone", auth_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, "Repository cloned successfully"
            else:
                return False, f"Git clone failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Git clone timeout (60s)"
        except FileNotFoundError:
            return False, "Git not found. Please install Git."
        except Exception as e:
            return False, f"Unexpected error: {e}"

    @staticmethod
    def clone_or_pull(repo_url: str, pat: str, target_dir: Path) -> Tuple[bool, str]:
        """
        Clone into target_dir, or pull if it is already a git working tree.
        """
        git_dir = target_dir / ".git"
        if git_dir.exists():
            return GitOperations.pull_repo(target_dir, pat)
        if target_dir.exists() and any(target_dir.iterdir()):
            return False, f"Directory exists and is not a git repo: {target_dir}"
        return GitOperations.clone_repo(repo_url, pat, target_dir)

    @staticmethod
    def pull_repo(repo_dir: Path, pat: str) -> Tuple[bool, str]:
        """
        Pull latest changes from repository
        
        Args:
            repo_dir: Repository directory
            pat: GitHub Personal Access Token
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Set credential helper to use PAT
            subprocess.run(
                ["git", "config", "credential.helper", "store"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            # Pull changes
            result = subprocess.run(
                ["git", "pull"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env={"GIT_ASKPASS": "echo", "GIT_USERNAME": "x-access-token", "GIT_PASSWORD": pat}
            )
            
            if result.returncode == 0:
                return True, "Repository updated successfully"
            else:
                return False, f"Git pull failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Git pull timeout (60s)"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    @staticmethod
    def push_repo(repo_dir: Path, pat: str, commit_message: str = "Update data") -> Tuple[bool, str]:
        """
        Push changes to repository
        
        Args:
            repo_dir: Repository directory
            pat: GitHub Personal Access Token
            commit_message: Commit message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_dir,
                capture_output=True,
                timeout=10
            )
            
            # Commit changes
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Push changes
            result = subprocess.run(
                ["git", "push"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env={"GIT_ASKPASS": "echo", "GIT_USERNAME": "x-access-token", "GIT_PASSWORD": pat}
            )
            
            if result.returncode == 0:
                return True, "Changes pushed successfully"
            else:
                return False, f"Git push failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Git push timeout (60s)"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    @staticmethod
    def check_git_installed() -> bool:
        """
        Check if Git is installed
        
        Returns:
            True if Git is available
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
