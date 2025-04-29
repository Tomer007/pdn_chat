import csv
from pathlib import Path
from datetime import datetime
import os

# CSV file location
CSV_DIR = Path(__file__).resolve().parent.parent.parent / "saved_results"
CSV_FILE = CSV_DIR / "pdn_users.csv"

# Ensure the directory exists
os.makedirs(CSV_DIR, exist_ok=True)

def init_csv():
    """Initialize the CSV file with headers if it doesn't exist"""
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'name', 'email', 'pdn_code', 'trait', 'energy', 'answers', 'created_at'])

def save_user(name: str, email: str, pdn_code: str, trait: str, energy: str, answers: str):
    """Save a new user to the CSV file"""
    # Get the next ID
    next_id = 1
    if CSV_FILE.exists():
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next_id = sum(1 for row in reader)  # Count existing rows
    
    # Prepare the new row
    new_row = [
        next_id,
        name,
        email,
        pdn_code,
        trait,
        energy,
        answers,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ]
    
    # Append the new row
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(new_row)

def load_all_users():
    """Load all users from the CSV file"""
    if not CSV_FILE.exists():
        return []
    
    users = []
    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users.append(row)
    
    return users

def get_user_stats():
    """Get statistics about users"""
    users = load_all_users()
    
    # Count by PDN code
    pdn_counts = {}
    trait_counts = {}
    energy_counts = {}
    
    for user in users:
        # Count PDN codes
        pdn_code = user['pdn_code']
        pdn_counts[pdn_code] = pdn_counts.get(pdn_code, 0) + 1
        
        # Count traits
        trait = user['trait']
        trait_counts[trait] = trait_counts.get(trait, 0) + 1
        
        # Count energy types
        energy = user['energy']
        energy_counts[energy] = energy_counts.get(energy, 0) + 1
    
    return {
        'total_users': len(users),
        'pdn_distribution': pdn_counts,
        'trait_distribution': trait_counts,
        'energy_distribution': energy_counts
    } 