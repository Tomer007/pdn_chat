import csv
from pathlib import Path
from datetime import datetime
import os

# CSV file location
CSV_DIR = Path(__file__).resolve().parent.parent.parent / "saved_results"
CSV_FILE = CSV_DIR / "user_info.csv"

# Ensure the directory exists
os.makedirs(CSV_DIR, exist_ok=True)

def init_user_info_csv():
    """Initialize the user info CSV file with headers if it doesn't exist"""
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'id', 'first_name', 'last_name', 'email', 'password',
                'mother_language', 'gender', 'job_title', 'birth_year',
                'remember_me', 'created_at'
            ])

def save_user_info(user_info):
    """Save user info to the CSV file"""
    # Get the next ID
    next_id = 1
    if CSV_FILE.exists():
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next_id = sum(1 for row in reader)  # Count existing rows
    
    # Prepare the new row
    new_row = [
        next_id,
        user_info.first_name,
        user_info.last_name,
        user_info.email,
        user_info.password,
        user_info.mother_language,
        user_info.gender,
        user_info.job_title,
        user_info.birth_year,
        int(user_info.remember_me) if user_info.remember_me is not None else 0,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ]
    
    # Append the new row
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(new_row)

def load_all_user_info():
    """Load all user info from the CSV file"""
    if not CSV_FILE.exists():
        return []
    
    users = []
    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users.append(row)
    
    return users 