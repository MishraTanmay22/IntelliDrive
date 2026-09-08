#!/usr/bin/env python3
"""
IntelliDrive Database Inspector
Run anytime with: python3 inspect_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'intellidrive.db')

def format_size(bytes_val):
    if not bytes_val or bytes_val == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def inspect_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("                      INTELLIDRIVE DATABASE INSPECTOR")
    print("=" * 80)

    # 1. Users Table
    try:
        cursor.execute("SELECT id, name, email, storage_quota_bytes, created_at FROM users")
        users = cursor.fetchall()
        print(f"\n[+] USERS TABLE ({len(users)} Registered):")
        print("-" * 80)
        print(f"{'#':<3} | {'User ID':<12} | {'Name':<20} | {'Email':<26} | {'Quota'}")
        print("-" * 80)
        for idx, u in enumerate(users, 1):
            quota_str = format_size(u['storage_quota_bytes']) if 'storage_quota_bytes' in u.keys() else "2.0 GB"
            user_id_short = str(u['id'])[:8] + "..." if len(str(u['id'])) > 10 else str(u['id'])
            print(f"{idx:<3} | {user_id_short:<12} | {str(u['name'])[:20]:<20} | {str(u['email'])[:26]:<26} | {quota_str}")
    except Exception as e:
        print(f"Error reading users: {e}")

    # 2. Files & Folders Table
    try:
        cursor.execute("SELECT id, user_id, name, file_type, size_bytes, is_folder, trashed FROM file_items")
        files = cursor.fetchall()
        print(f"\n[+] FILE_ITEMS TABLE ({len(files)} Total Records):")
        print("-" * 80)
        print(f"{'#':<3} | {'Type':<8} | {'Size':<10} | {'Trash':<5} | {'File/Folder Name'}")
        print("-" * 80)
        if not files:
            print("  (No files uploaded yet)")
        for idx, f in enumerate(files, 1):
            size_str = "FOLDER" if f['is_folder'] else format_size(f['size_bytes'])
            trashed_str = "YES" if f['trashed'] else "NO"
            print(f"{idx:<3} | {str(f['file_type'])[:8]:<8} | {size_str:<10} | {trashed_str:<5} | {f['name']}")
    except Exception as e:
        print(f"Error reading file_items: {e}")

    print("\n" + "=" * 80 + "\n")
    conn.close()

if __name__ == '__main__':
    inspect_database()
