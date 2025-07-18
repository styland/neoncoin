import sqlite3

conn = sqlite3.connect("neoncoin.db")
cursor = conn.cursor()

# Add the missing column
cursor.execute("ALTER TABLE balances ADD COLUMN daily_bonus_date TEXT")

conn.commit()
conn.close()

print("Column 'daily_bonus_date' added successfully.")
