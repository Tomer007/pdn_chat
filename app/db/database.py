from .csv_handler import init_csv, save_user, load_all_users, get_user_stats
from .user_info_csv import init_user_info_csv, save_user_info, load_all_user_info

# Initialize CSV files
init_csv()
init_user_info_csv()

# Re-export the functions
save_user_to_db = save_user
load_all_users_from_db = load_all_users
get_user_stats_from_db = get_user_stats
save_user_info_to_db = save_user_info
load_all_user_info_from_db = load_all_user_info
