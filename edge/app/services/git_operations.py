"""Git operations for station provisioning and snapshot sync."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple


class GitOperations:
    """Handle Git operations with PAT or SSH deploy key authentication"""

    # ── SSH helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _ssh_env(private_key_pem: str) -> tuple[dict, str]:
        """
        Write SSH private key to a temp file and return GIT_SSH_COMMAND env.
        Caller is responsible for deleting the temp file.

        Returns:
            (env_dict, tmp_key_path)
        """
        # Đảm bảo key kết thúc bằng newline — PEM format yêu cầu
        key_content = private_key_pem.strip() + "\n"

        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False, prefix="carevl_ssh_",
            newline="\n",   # LF, không phải CRLF — OpenSSH không chấp nhận CRLF
        )
        tmp.write(key_content)
        tmp.flush()
        tmp.close()

        # Windows: dùng icacls để set permission đúng
        # OpenSSH trên Windows từ chối key nếu file có quyền quá rộng
        import platform
        if platform.system() == "Windows":
            import subprocess as _sp
            username = os.environ.get("USERNAME", "")
            _sp.run(
                ["icacls", tmp.name, "/inheritance:r",
                 "/grant:r", f"{username}:(R)"],
                capture_output=True,
            )
        else:
            os.chmod(tmp.name, 0o600)

        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = (
            f'ssh -i "{tmp.name}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
        )
        return env, tmp.name

    @staticmethod
    def _ssh_url(https_url: str) -> str:
        """Convert https://github.com/owner/repo to git@github.com:owner/repo.git"""
        # https://github.com/owner/repo  →  git@github.com:owner/repo.git
        path = https_url.replace("https://github.com/", "")
        if not path.endswith(".git"):
            path += ".git"
        return f"git@github.com:{path}"

    # ── Clone ──────────────────────────────────────────────────────────────────

    @staticmethod
    def clone_repo(
        repo_url: str,
        target_dir: Path,
        pat: str | None = None,
        ssh_private_key: str | None = None,
    ) -> Tuple[bool, str]:
        """
        Clone repository using PAT or SSH deploy key.

        Provide exactly one of pat or ssh_private_key.
        """
        try:
            # Backward compatibility: some legacy callers still pass
            # clone_repo(repo_url, pat, repo_dir).
            if isinstance(target_dir, str) and isinstance(pat, Path):
                target_dir, pat = pat, target_dir

            target_dir.parent.mkdir(parents=True, exist_ok=True)

            if ssh_private_key:
                env, tmp_key = GitOperations._ssh_env(ssh_private_key)
                url = GitOperations._ssh_url(repo_url)
                try:
                    result = subprocess.run(
                        ["git", "clone", url, str(target_dir)],
                        capture_output=True, text=True, timeout=60, env=env,
                    )
                finally:
                    Path(tmp_key).unlink(missing_ok=True)
            elif pat:
                auth_url = repo_url.replace("https://", f"https://{pat}@")
                result = subprocess.run(
                    ["git", "clone", auth_url, str(target_dir)],
                    capture_output=True, text=True, timeout=60,
                )
            else:
                return False, "Provide pat or ssh_private_key"

            if result.returncode == 0:
                return True, "Repository cloned successfully"
            return False, f"Git clone failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Git clone timeout (60s)"
        except FileNotFoundError:
            return False, "Git not found. Please install Git."
        except Exception as e:
            return False, f"Unexpected error: {e}"

    @staticmethod
    def clone_or_pull(
        repo_url: str,
        target_dir: Path,
        pat: str | None = None,
        ssh_private_key: str | None = None,
    ) -> Tuple[bool, str]:
        """Clone or pull depending on whether repo already exists."""
        git_dir = target_dir / ".git"
        if git_dir.exists():
            return GitOperations.pull_repo(target_dir, pat=pat, ssh_private_key=ssh_private_key)
        if target_dir.exists() and any(target_dir.iterdir()):
            return False, f"Directory exists and is not a git repo: {target_dir}"
        return GitOperations.clone_repo(repo_url, target_dir, pat=pat, ssh_private_key=ssh_private_key)

    # ── Pull ───────────────────────────────────────────────────────────────────

    @staticmethod
    def pull_repo(
        repo_dir: Path,
        pat: str | None = None,
        ssh_private_key: str | None = None,
    ) -> Tuple[bool, str]:
        """Pull latest changes."""
        try:
            if ssh_private_key:
                env, tmp_key = GitOperations._ssh_env(ssh_private_key)
                try:
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=repo_dir, capture_output=True, text=True, timeout=60, env=env,
                    )
                finally:
                    Path(tmp_key).unlink(missing_ok=True)
            else:
                env = {"GIT_ASKPASS": "echo", "GIT_USERNAME": "x-access-token", "GIT_PASSWORD": pat or ""}
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=repo_dir, capture_output=True, text=True, timeout=60, env=env,
                )

            if result.returncode == 0:
                return True, "Repository updated successfully"
            return False, f"Git pull failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Git pull timeout (60s)"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    # ── Push ───────────────────────────────────────────────────────────────────

    @staticmethod
    def push_repo(
        repo_dir: Path,
        commit_message: str = "Update data",
        pat: str | None = None,
        ssh_private_key: str | None = None,
    ) -> Tuple[bool, str]:
        """Add, commit, and push changes."""
        try:
            subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, timeout=10)
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_dir, capture_output=True, text=True, timeout=10,
            )

            if ssh_private_key:
                env, tmp_key = GitOperations._ssh_env(ssh_private_key)
                try:
                    result = subprocess.run(
                        ["git", "push"],
                        cwd=repo_dir, capture_output=True, text=True, timeout=60, env=env,
                    )
                finally:
                    Path(tmp_key).unlink(missing_ok=True)
            else:
                env = {"GIT_ASKPASS": "echo", "GIT_USERNAME": "x-access-token", "GIT_PASSWORD": pat or ""}
                result = subprocess.run(
                    ["git", "push"],
                    cwd=repo_dir, capture_output=True, text=True, timeout=60, env=env,
                )

            if result.returncode == 0:
                return True, "Changes pushed successfully"
            return False, f"Git push failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Git push timeout (60s)"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    @staticmethod
    def push_snapshot_file(
        repo_dir: Path,
        snapshot_path: Path,
        ssh_private_key: str | None = None,
        pat: str | None = None,
    ) -> Tuple[bool, str]:
        """
        Copy snapshot and sidecar into repo snapshots/ then commit + push.
        """
        try:
            if not snapshot_path.exists():
                return False, f"Snapshot not found: {snapshot_path}"

            snapshots_dir = repo_dir / "snapshots"
            snapshots_dir.mkdir(parents=True, exist_ok=True)

            dest_snapshot = snapshots_dir / snapshot_path.name
            shutil.copy2(snapshot_path, dest_snapshot)
            tracked_paths = [str(dest_snapshot.relative_to(repo_dir))]

            sidecar_path = snapshot_path.with_suffix("").with_suffix(".json")
            if sidecar_path.exists():
                dest_sidecar = snapshots_dir / sidecar_path.name
                shutil.copy2(sidecar_path, dest_sidecar)
                tracked_paths.append(str(dest_sidecar.relative_to(repo_dir)))

            subprocess.run(
                ["git", "config", "user.name", "CareVL Edge"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "config", "user.email", "carevl-edge@local.invalid"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            add_result = subprocess.run(
                ["git", "add", *tracked_paths],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if add_result.returncode != 0:
                return False, f"Git add failed: {add_result.stderr}"

            commit_result = subprocess.run(
                ["git", "commit", "-m", f"Add snapshot {snapshot_path.name}"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if commit_result.returncode != 0:
                stderr = (commit_result.stderr or "").strip()
                stdout = (commit_result.stdout or "").strip()
                if "nothing to commit" in stderr.lower() or "nothing to commit" in stdout.lower():
                    return True, "Snapshot already synced"
                return False, f"Git commit failed: {stderr or stdout}"

            if ssh_private_key:
                env, tmp_key = GitOperations._ssh_env(ssh_private_key)
                try:
                    result = subprocess.run(
                        ["git", "push"],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        env=env,
                    )
                finally:
                    Path(tmp_key).unlink(missing_ok=True)
            else:
                env = {
                    "GIT_ASKPASS": "echo",
                    "GIT_USERNAME": "x-access-token",
                    "GIT_PASSWORD": pat or "",
                }
                result = subprocess.run(
                    ["git", "push"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env,
                )

            if result.returncode == 0:
                return True, "Snapshot pushed successfully"
            return False, f"Git push failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Git snapshot push timeout"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    # ── Misc ───────────────────────────────────────────────────────────────────

    @staticmethod
    def check_git_installed() -> bool:
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
