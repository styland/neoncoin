import sqlite3
import hashlib
import random

def generate_account_number():
    return str(random.randint(1000000000, 9999999999))

# Replace these with your desired admin credentials
username = 'admin'
email = 'admin@example.com'
password = 'admin123'

# Hash the password
hashed_password = hashlib.sha256(password.encode()).hexdigest()
account_number = generate_account_number()

conn = sqlite3.connect('neoncoin.db')
cursor = conn.cursor()

# Insert admin user
cursor.execute('''
    INSERT INTO users (username, email, password, account_number, verification_code, verified, role, is_banned)
    VALUES (?, ?, ?, ?, ?, 1, 'admin', 0)
''', (username, email, hashed_password, account_number, '000000'))

# Insert balance row
cursor.execute('''
    INSERT INTO balances (user_id, neo, neons, neolites)
    VALUES ((SELECT id FROM users WHERE email = ?), 0, 0, 0)
''', (email,))

conn.commit()
conn.close()

print(f"✅ Admin user '{username}' created with account number {account_number}")
