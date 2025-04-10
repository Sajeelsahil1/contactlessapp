import sqlite3

DB_FILE = "fingerprints.db"

def clear_fingerprint_database():
    """Delete all fingerprints from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM fingerprints")  # Remove all records
    conn.commit()
    conn.close()
    print("All fingerprints deleted successfully.")

# Run the function
clear_fingerprint_database()
