import sqlite3
import json
import csv
import numpy as np
import os
import threading  # For async backup

# Database file
DB_FILE = "fingerprints.db"
CSV_BACKUP_FILE = "fingerprint_backup.csv"

# Initialize database connection
def get_db_connection():
    """Returns a new database connection from the pool."""
    return sqlite3.connect(DB_FILE, check_same_thread=False)

# Ensure the database exists
conn = get_db_connection()
cursor = conn.cursor()

# Create the fingerprints table with an index for faster lookups
cursor.execute("""
    CREATE TABLE IF NOT EXISTS fingerprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        descriptors TEXT
    )
""")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON fingerprints(username);")  # Speed up queries
conn.commit()
conn.close()

def save_fingerprint(username, descriptors):
    """Save fingerprint descriptors in SQLite and update CSV backup asynchronously."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure ORB descriptors are stored as a NumPy uint8 array
        descriptors["orb"] = np.array(descriptors["orb"], dtype=np.uint8).tolist()

        # Convert descriptors dictionary into JSON
        descriptors_json = json.dumps(descriptors)

        cursor.execute("INSERT INTO fingerprints (username, descriptors) VALUES (?, ?)", 
                       (username, descriptors_json))
        conn.commit()
        conn.close()

        # Run CSV backup in a separate thread to avoid blocking
        threading.Thread(target=backup_to_csv, daemon=True).start()

        return "Fingerprint saved successfully."
    except sqlite3.IntegrityError:
        return "User already registered."
    except Exception as e:
        return f"Error saving fingerprint: {str(e)}"

def get_fingerprints():
    """Retrieve all fingerprints and convert descriptors back to NumPy arrays efficiently."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, descriptors FROM fingerprints")
    fingerprints = cursor.fetchall()
    conn.close()

    processed_fingerprints = []
    for username, descriptor_json in fingerprints:
        try:
            data = json.loads(descriptor_json)
            descriptors = np.array(data["orb"], dtype=np.uint8)  # Convert ORB descriptors back to NumPy
            minutiae_points = data["minutiae"]  # Minutiae points remain as a list

            processed_fingerprints.append((username, {"orb": descriptors, "minutiae": minutiae_points}))
        except Exception as e:
            print(f"Error processing fingerprint for {username}: {e}")

    return processed_fingerprints

def backup_to_csv():
    """Backup fingerprint data to a CSV file asynchronously."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT username, descriptors FROM fingerprints")
        fingerprints = cursor.fetchall()
        conn.close()

        with open(CSV_BACKUP_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Username", "Descriptors"])  # Header row

            for username, descriptor_json in fingerprints:
                writer.writerow([username, descriptor_json])
    except Exception as e:
        print(f"Error backing up CSV: {e}")

def delete_fingerprint(username):
    """Delete a fingerprint record from SQLite and update CSV backup asynchronously."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM fingerprints WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    # Run CSV backup in a separate thread
    threading.Thread(target=backup_to_csv, daemon=True).start()
    
    return f"Fingerprint record for {username} deleted."

# Initial CSV backup to ensure data is up-to-date
threading.Thread(target=backup_to_csv, daemon=True).start()
