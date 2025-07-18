import sqlite3

DB_PATH = 'your_database.db'  # change to your actual DB path

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add spins_available and last_spin_update if they don't exist
    try:
        cursor.execute("ALTER TABLE balances ADD COLUMN spins_available INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        print("Column spins_available already exists")

    try:
        cursor.execute("ALTER TABLE balances ADD COLUMN last_spin_update TEXT")
    except sqlite3.OperationalError:
        print("Column last_spin_update already exists")

    # Add daily_bonus_date and weekly_bonus_date to track last claimed date
    try:
        cursor.execute("ALTER TABLE balances ADD COLUMN daily_bonus_date TEXT")
    except sqlite3.OperationalError:
        print("Column daily_bonus_date already exists")

    try:
        cursor.execute("ALTER TABLE balances ADD COLUMN weekly_bonus_date TEXT")
        cursor.execute("ALTER TABLE balances ADD COLUMN spins_available INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        print("Column weekly_bonus_date already exists")

    conn.commit()
    conn.close()
    print("Database updated successfully.")





if __name__ == "__main__":
    update_db()
