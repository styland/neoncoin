

import sqlite3

conn = sqlite3.connect('neoncoin.db')  # Replace with your database file
cursor = conn.cursor()

# Add the missing column
cursor.execute("ALTER TABLE balances ADD COLUMN last_spin_update TEXT")

# Optionally, set it to the current time for all users (ISO format string)
from datetime import datetime
now = datetime.utcnow().isoformat()
cursor.execute("UPDATE balances SET last_spin_update = ?", (now,))

conn.commit()
conn.close()
