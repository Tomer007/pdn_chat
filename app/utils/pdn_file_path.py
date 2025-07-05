import os
from pathlib import Path
from typing import Optional


class PDNFilePath:
    """Utility class for handling PDN file paths and user directories."""

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize PDNFilePath utility.
        
        Args:
            base_dir: Base directory for saved results. Defaults to 'saved_results'
        """
        self.base_dir = Path(base_dir or os.getenv('ANSWERS_DIR', 'saved_results'))

    def get_base_dir(self) -> Path:
        """
        Get base directory.
        
        Returns:
            Path object pointing to the base directory
        """
        return self.base_dir

    def get_user_dir(self, user_email: str) -> Path:
        """
        Get or create user directory based on email.
        
        Args:
            user_email: User's email address
            
        Returns:
            Path object pointing to the user's directory
        """
        # Create safe username from email
        safe_username = "".join(c for c in user_email if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_username = safe_username.replace(' ', '_')

        # Create user directory path
        user_dir = self.base_dir / safe_username

        # Create directory if it doesn't exist
        user_dir.mkdir(parents=True, exist_ok=True)

        return user_dir

    def get_user_file_path(self, user_email: str, filename: str) -> Path:
        """
        Get file path within user directory.
        
        Args:
            user_email: User's email address
            filename: Name of the file
            
        Returns:
            Path object pointing to the file within user directory
        """
        user_dir = self.get_user_dir(user_email)
        file_path = user_dir / filename

        return file_path

    def ensure_user_dir_exists(self, user_email: str) -> Path:
        """
        Ensure user directory exists and return its path.
        
        Args:
            user_email: User's email address
            
        Returns:
            Path object pointing to the user's directory
        """
        return self.get_user_dir(user_email)

    def list_user_files(self, user_email: str, pattern: str = "*") -> list[Path]:
        """
        List files in user directory matching pattern.
        
        Args:
            user_email: User's email address
            pattern: File pattern to match (default: all files)
            
        Returns:
            List of Path objects for matching files
        """
        user_dir = self.get_user_dir(user_email)
        return list(user_dir.glob(pattern))


