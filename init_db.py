import sqlite3

def init_db():
    conn = sqlite3.connect('neoncoin.db')
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            verification_code TEXT,
            verified INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            is_banned INTEGER DEFAULT 0,
            banned_until TEXT,
            timeout_until TEXT
        )
    ''')

    # BALANCES TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            user_id INTEGER PRIMARY KEY,
            neo INTEGER DEFAULT 0,
            neons INTEGER DEFAULT 0,
            neolites INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # TRANSACTIONS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            currency TEXT NOT NULL,
            amount INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully with extended admin support.")

if __name__ == '__main__':
    init_db()
