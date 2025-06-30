import csv
import os
from typing import Dict, Any
from app.utils.pdn_file_path import PDNFilePath
import json
from app.utils.pdn_file_path import PDNFilePath

class CSVMetadataHandler:
    """Utility class for handling user metadata CSV operations."""
    
    def __init__(self):
        """
        Initialize CSV metadata handler.
        
        Args:
            csv_filename: Name of the CSV file (default: user_metadata.csv)
        """

        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_base_dir()
        self.csv_filename = user_dir / "user_metadata.csv"

        self.headers = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "birth_year",
            "mother_language",
            "gender",
            "education",
            "job_title",
            "audio_1_path",
            "audio_2_path",
            "audio_3_path",
            "answer_path"
        ]
    
    def ensure_csv_exists(self) -> None:
        """Create CSV file with headers if it doesn't exist."""
        pdn_file_path = PDNFilePath()
        base_dir = pdn_file_path.get_base_dir()
        csv_file_path = base_dir / self.csv_filename
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(self.headers)
    
    def append_user_metadata(self, user_data: Dict[str, Any]) -> bool:
        """
        Append user metadata to CSV file.
        
        Args:
            user_data: Dictionary containing user metadata with Hebrew keys
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure CSV file exists with headers
            self.ensure_csv_exists()
            
            # Prepare row data in correct order
            row_data = []
            for header in self.headers:
                row_data.append(user_data.get(header, ""))
            
            # Append new row to CSV
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row_data)
            
            return True
            
        except Exception as e:
            print(f"Error appending metadata to CSV: {e}")
            return False
    
    def read_all_metadata(self) -> list[Dict[str, str]]:
        """
        Read all metadata from CSV file.
        
        Returns:
            List of dictionaries containing user metadata
        """
        try:
            if not os.path.exists(self.csv_filename):
                return []
            
            metadata_list = []
            with open(self.csv_filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    metadata_list.append(dict(row))
            
            return metadata_list
            
        except Exception as e:
            print(f"Error reading metadata from CSV: {e}")
            return []
    
    def get_user_files(self, email: str, file_type: str) -> Dict[str, Any]:
        """
        Find specific user metadata by email.
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary containing user metadata or None if not found
        """
        try:
            pdn_file_path = PDNFilePath()
            user_dir = pdn_file_path.get_user_dir(email)
            csv_file_path = pdn_file_path.find(user_dir, file_type) 

            # Check if csv_file_path is None before calling os.path.exists
            if csv_file_path is None:
                return None
            
            if not os.path.exists(csv_file_path):
                return None
            
            with open(csv_file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            return data
            
        except Exception as e:
            print(f"Error finding user metadata: {e}")
            return None
        
    def get_user_audio_path(self, email: str, file_type: str):
        """
        Get user audio path.
        
        Args:
            email: User's email address
            file_type: Type of file to find
        """
        try:
            pdn_file_path = PDNFilePath()
            user_dir = pdn_file_path.get_user_dir(email)
            file_path = pdn_file_path.find(user_dir, file_type) 

            # Check if file_path is None before calling os.path.exists
            if file_path is None:
                return None
            
            if not os.path.exists(file_path):
                return None
            
            return file_path
            
        except Exception as e:
            print(f"Error finding user metadata: {e}")
            return None
    
    def update_user_metadata(self, email: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update existing user metadata.
        
        Args:
            email: User's email address
            updated_data: Dictionary containing updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.csv_filename):
                return False
            
            # Read all data
            all_data = self.read_all_metadata()
            
            # Find and update the specific user
            updated = False
            for i, row in enumerate(all_data):
                if row.get("אימייל") == email:
                    # Update with new data while preserving existing data
                    for key, value in updated_data.items():
                        if key in self.headers:
                            row[key] = value
                    all_data[i] = row
                    updated = True
                    break
            
            if not updated:
                return False
            
            # Write back all data
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(all_data)
            
            return True
            
        except Exception as e:
            print(f"Error updating user metadata: {e}")
            return False
    