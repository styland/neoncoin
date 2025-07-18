import sqlite3

conn = sqlite3.connect('neoncoin.db')  # Update if your DB is named differently
cursor = conn.cursor()

# Add the column only if it doesn't already exist
try:
    #cursor.execute('ALTER TABLE balances ADD COLUMN weekly_bonus_date TEXT')
    #cursor.execute('ALTER TABLE balances ADD COLUMN daily_bonus_date TEXT')
    #cursor.execute('ALTER TABLE balances ADD COLUMN last_spin_time TEXT')
    #cursor.execute('ALTER TABLE balances ADD COLUMN can_spin INTEGER DEFAULT 1')
    print("former works")
    cursor.execute('ALTER TABLE balances ADD COLUMN spins INTEGER DEFAULT 5')
    print("new change applied")
except sqlite3.OperationalError as e:
    print("Column may already exist:", e)

conn.commit()
conn.close()
