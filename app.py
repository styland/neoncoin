from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
import sqlite3
import hashlib
from datetime import datetime
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from paystackapi.transaction import Transaction
from paystackapi.paystack import Paystack
import uuid

def send_verification_email(to_email, code):
    sender_email = "rotimidamilola2011@gmail.com"
    sender_password = "fmxrtqldmwmbucsi"

    subject = "Your NeonCoin Verification Code"
    body = f"""
    <html>
        <body style="font-family: Arial; background-color: #111; color: #fff; padding: 20px;">
            <h2 style="color: #0ff;">NeonCoin Email Verification</h2>
            <p>Thank you for signing up! Your verification code is:</p>
            <h1 style="color: #0ff;">{code}</h1>
            <p>Please enter this code on the verification page to complete your registration.</p>
        </body>
    </html>
    """

    # Create the email
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    # Send it via Gmail's SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, message.as_string())
print("preparing modules")
app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
app.secret_key = 'supersecretkey'

DATABASE = 'neoncoin.db'
print("initializing database")

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))


def generate_account_number():
    return ''.join(random.choices(string.digits, k=10))


@app.route('/')
def index():
    print("homepage visited")
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        account_number = generate_account_number()
        verification_code = generate_verification_code()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password, account_number, verification_code, verified)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (username, email, hashed_password, account_number, verification_code))
            conn.commit()
            conn.close()
            session['pending_email'] = email
            session['verification_code'] = verification_code
            session['user_id'] = cursor.lastrowid  # right after inserting the user
            session['email'] = email
            send_verification_email(email,verification_code)
            flash(message="successfully sent verification email",category="success")
            print(verification_code)
            return redirect(url_for('emailconfirm'))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "danger")
            conn.close()

    return render_template('register.html')


@app.route('/emailconfirm', methods=['GET', 'POST'])
def emailconfirm():
    

    if request.method == 'POST':
        input_code = request.form.get("code")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT verification_code FROM users WHERE id = ?", (session['user_id'],))
        row = cursor.fetchone()

        if row and input_code == row['verification_code']:
            cursor.execute("UPDATE users SET verified = 1 WHERE id = ?", (session['user_id'],))
            conn.commit()
            conn.close()
            flash("✅ Account verified successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            
            conn.close()
            flash("❌ Invalid verification code. Please try again.", "danger")
    return render_template("emailconfirm.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
        user = cursor.fetchone()
   
        if user :
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['is_admin'] = user['role'] == 'admin'
            session['account_number'] = user['account_number']
            flash('Login successful',category='success')
            return redirect(url_for('dashboard'))
        else:
            flash(message='Login failed',category='danger')
    return render_template('login.html')


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        verification_code = generate_verification_code()
        print(verification_code)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            cursor.execute('UPDATE users SET verification_code = ? WHERE email = ?', (verification_code, email))
            conn.commit()
            send_verification_email(email,verification_code)
            session['reset_email'] = email
            session['verification_code'] = verification_code
            flash(message="mail sent successfully",category="success")
            return redirect(url_for('reset_password'))
            
        else:
            flash("Email not found.", "danger")
        print(email,verification_code)
    return render_template('forgotpassword.html')


@app.route('/buy', methods=['GET', 'POST'])
def buy():
    packs = {
        'starter': {'price': 5000, 'neo': 50, 'neons': 200, 'neolites': 500, 'chance': 60},
        'value':   {'price': 10000, 'neo': 110, 'neons': 400, 'neolites': 1000, 'chance': 30},
        'mega':    {'price': 20000, 'neo': 250, 'neons': 1000, 'neolites': 2500, 'chance': 8},
        'ultimate':{'price': 50000, 'neo': 700, 'neons': 2500, 'neolites': 7000, 'chance': 2}
    }

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure balances row exists
    cursor.execute('''
        INSERT INTO balances (user_id, neo, neons, neolites, spins_available)
        SELECT ?, 0, 0, 0, 0
        WHERE NOT EXISTS (SELECT 1 FROM balances WHERE user_id = ?)
    ''', (user_id, user_id))
    conn.commit()

    # 🌟 Update spins if needed
    spins, next_spin_time = update_spin_availability(user_id)

    if request.method == 'POST':
        selected_pack = random.choice(list(packs.keys()))
        selected_pack_key = selected_pack

        if not selected_pack_key or selected_pack_key not in packs:
            flash("Invalid or missing pack selection.", "danger")
            return redirect(url_for('buy'))

        selected_pack = packs[selected_pack_key]

        # Update balances
        cursor.execute('''
            UPDATE balances SET 
                spins_available = spins_available - ?,
                neo = neo + ?, 
                neons = neons + ?, 
                neolites = neolites + ?
            WHERE user_id = ?
        ''', (
            1,
            selected_pack['neo'],
            selected_pack['neons'],
            selected_pack['neolites'],
            user_id
        ))

        # Log the transaction
        cursor.execute('''
            INSERT INTO transactions (sender_id, receiver_id, currency, amount, timestamp)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', ("system", user_id, 'pack:' + selected_pack_key, selected_pack['price']))

        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()

        flash(f"Purchase successful! You received a {selected_pack_key.capitalize()} pack.", "success")
        return redirect(url_for('receipt', transaction_id=transaction_id))

    conn.close()
    return render_template('buy.html', spins=spins, max_spins=MAX_SPINS, next_spin_time=next_spin_time,pack_names=["starter","value","mega","ultimate"], prize=None)


@app.route('/dash', methods=['GET', 'POST'])
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the user balance
    cursor.execute('SELECT neo, neons, neolites FROM balances WHERE user_id = ?', (user_id,))
    balances = cursor.fetchone()

    if not balances:
        # Create initial balance row if not exists
        cursor.execute('INSERT INTO balances (user_id, neo, neons, neolites) VALUES (?, 0, 0, 0)', (user_id,))
        conn.commit()
        cursor.execute('SELECT neo, neons, neolites FROM balances WHERE user_id = ?', (user_id,))
        balances = cursor.fetchone()

    # Handle the filter from the form
    if request.method == 'POST':
        filter_type = request.form.get('filter_type', '')
        filter_currency = request.form.get('filter_currency', '')
        filter_date_start = request.form.get('filter_date_start', '')
        filter_date_end = request.form.get('filter_date_end', '')

        query = '''
            SELECT t.*, u.username AS other_user
            FROM transactions t
            LEFT JOIN users u ON u.id = 
                CASE 
                    WHEN t.sender_id = ? THEN t.receiver_id 
                    ELSE t.sender_id 
                END
            WHERE t.sender_id = ? OR t.receiver_id = ?
        '''

        params = [user_id, user_id, user_id]

        # Apply filters based on form input
        if filter_type:
            if filter_type == 'sent':
                query += " AND t.sender_id = ?"
            elif filter_type == 'received':
                query += " AND t.receiver_id = ?"
            params.append(user_id)

        if filter_currency:
            query += " AND t.currency = ?"
            params.append(filter_currency)

        if filter_date_start:
            query += " AND t.timestamp >= ?"
            params.append(filter_date_start)

        if filter_date_end:
            query += " AND t.timestamp <= ?"
            params.append(filter_date_end)

        query += " ORDER BY t.timestamp DESC LIMIT 10"

        cursor.execute(query, tuple(params))
        transactions = cursor.fetchall()

    else:
        # Default query for all transactions without filtering
        cursor.execute('''
            SELECT t.*, u.username AS other_user
            FROM transactions t
            LEFT JOIN users u ON u.id = 
                CASE 
                    WHEN t.sender_id = ? THEN t.receiver_id 
                    ELSE t.sender_id 
                END
            WHERE t.sender_id = ? OR t.receiver_id = ?
            ORDER BY t.timestamp DESC LIMIT 10
        ''', (user_id, user_id, user_id))
        transactions = cursor.fetchall()

    conn.close()

    return render_template('dash.html', user_balances=balances, transactions=transactions)
from flask import session

def get_current_user():
    """
    Return the currently‐logged in user row (sqlite3.Row) or None if not logged in.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, b.neo, b.neons, b.neolites
        FROM users u
        LEFT JOIN balances b ON u.id = b.user_id
        WHERE u.id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template('profile.html', user=user)

@app.route('/about')
def about():
    return render_template('about.html')
@app.route("/resend-verification")
def reset():
    email=session.get("email")
    new = generate_verification_code()
    session['verification_code'] = new
    send_verification_email(email,new)
    flash(message='email has been resent',category='info')
    print(new)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET verification_code = ? WHERE email = ?', (new, email))
    conn.commit()

    return  redirect(url_for('emailconfirm'))
@app.route("/logout")
def logout():
    session.clear()
    return index()
@app.route('/trade', methods=['GET', 'POST'])
@app.route('/trade', methods=['GET'])
def trade():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    return render_template('trade.html')
@app.route('/confirm_trade', methods=['POST'])
def confirm_trade():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    receiver_acc = request.form.get('receiver')
    currency = request.form.get('currency')
    amount = int(request.form.get('amount'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validate receiver
    cursor.execute('SELECT id, username FROM users WHERE account_number = ?', (receiver_acc,))
    receiver = cursor.fetchone()
    if not receiver:
        conn.close()
        flash('Receiver not found.', 'danger')
        return redirect(url_for('trade'))

    receiver_id = receiver['id']
    reciever_username = receiver['username']

    # Validate balance
    cursor.execute(f'SELECT {currency} FROM balances WHERE user_id = ?', (user_id,))
    sender_balance = cursor.fetchone()
    if not sender_balance or sender_balance[currency] < amount:
        conn.close()
        flash('Insufficient balance.', 'danger')
        return redirect(url_for('trade'))

    conn.close()

    return render_template('confirm_trade.html',
                           current_user=get_current_user(),
                           recipient=receiver_acc,
                           currency=currency,
                           reciever_username = reciever_username,
                           amount=amount)
@app.route('/finalize_trade', methods=['POST'])
def finalize_trade():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    receiver_acc = request.form['recipient']
    currency = request.form['currency']
    amount = int(request.form['amount'])

    conn = get_db_connection()
    cursor = conn.cursor()

    # Confirm receiver
    cursor.execute('SELECT id , username FROM users WHERE account_number = ?', (receiver_acc,))
    receiver = cursor.fetchone()
    if not receiver:
        conn.close()
        flash('Receiver not found.', 'danger')
        return redirect(url_for('trade'))

    receiver_id = receiver['id']
    reciever_username = receiver['username']
    # Confirm balance
    cursor.execute(f'SELECT {currency} FROM balances WHERE user_id = ?', (user_id,))
    sender_balance = cursor.fetchone()
    if not sender_balance or sender_balance[currency] < amount:
        conn.close()
        flash('Insufficient balance.', 'danger')
        return redirect(url_for('trade'))

    # Perform trade
    cursor.execute(f'UPDATE balances SET {currency} = {currency} - ? WHERE user_id = ?', (amount, user_id))
    cursor.execute(f'''
        INSERT INTO balances (user_id, neo, neons, neolites)
        SELECT ?, 0, 0, 0
        WHERE NOT EXISTS (SELECT 1 FROM balances WHERE user_id = ?)
    ''', (receiver_id, receiver_id))

    cursor.execute(f'UPDATE balances SET {currency} = {currency} + ? WHERE user_id = ?', (amount, receiver_id))

    cursor.execute('''
        INSERT INTO transactions (sender_id, receiver_id, currency, amount, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', (user_id, receiver_id, currency, amount))

    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return redirect(url_for('receipt', transaction_id=transaction_id))

from datetime import datetime, timedelta

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        flash('You are not authorized to access the admin panel.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all users and their balances using a JOIN
    cursor.execute('''
        SELECT users.account_number, users.username, users.email, users.id, users.is_banned, users.timeout_until,
               balances.neo, balances.neons, balances.neolites 
        FROM users
        JOIN balances ON users.id = balances.user_id
    ''')
    users = cursor.fetchall()

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        account_number = request.form.get('account_number')

        # Get user_id from account number
        cursor.execute("SELECT id FROM users WHERE account_number = ?", (account_number,))
        user = cursor.fetchone()

        if not user:
            flash('Account number not found.', 'danger')
            return redirect(url_for('admin'))

        user_id = user['id']

        if form_type == 'update':
            neo = request.form.get('neo')
            neons = request.form.get('neons')
            neolites = request.form.get('neolites')

            cursor.execute('''
                UPDATE balances SET neo = ?, neons = ?, neolites = ? WHERE user_id = ?
            ''', (neo, neons, neolites, user_id))
            conn.commit()
            flash('Balance updated successfully.', 'success')

    if not session.get('is_admin'):
        flash('You are not authorized to access the admin panel.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        form_type = request.form['form_type']

        if form_type == 'update':
            # your balance update logic
            pass

        elif form_type == 'timeout':
            # your timeout logic
            pass

        elif form_type == 'give_spins':
            account_number = request.form['account_number']
            spins_to_give = int(request.form['spins'])

            cursor.execute("SELECT id FROM users WHERE account_number = ?", (account_number,))
            user = cursor.fetchone()

            if user:
                user_id = user['id']
                cursor.execute('''
                    UPDATE balances
                    SET spins_available = spins_available + ?
                    WHERE user_id = ?
                ''', (spins_to_give, user_id))
                conn.commit()
                flash(f"Gave {spins_to_give} spin(s) to account {account_number}.", "success")
            else:
                flash("User not found.", "danger")       

        elif form_type == 'ban':
            cursor.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (user_id,))
            conn.commit()
            flash('User has been banned.', 'warning')

        elif form_type == 'timeout':
            minutes = int(request.form.get('duration'))
            timeout_until = datetime.utcnow() + timedelta(minutes=minutes)
            cursor.execute('UPDATE users SET timeout_until = ? WHERE id = ?', (timeout_until, user_id))
            conn.commit()
            flash(f'User has been timed out for {minutes} minutes.', 'warning')

        elif form_type == 'edit_user':
            new_username = request.form.get('new_username')
            new_email = request.form.get('new_email')
            new_account = request.form.get('new_account_number')

            cursor.execute('''
                UPDATE users SET username = ?, email = ?, account_number = ? WHERE id = ?
            ''', (new_username, new_email, new_account, user_id))
            conn.commit()
            flash('User details updated.', 'info')

        return redirect(url_for('admin'))

    return render_template('admin.html' )
from datetime import datetime, timedelta

@app.route('/admin/ban', methods=['POST'])
def ban_user():
    if not session.get('is_admin'):
        flash('You are not authorized to ban users.', 'danger')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    account_number = request.form['account_number']
    ban_duration = int(request.form['duration'])  # Duration in minutes

    cursor.execute("SELECT id FROM users WHERE account_number = ?", (account_number,))
    user = cursor.fetchone()

    if user:
        user_id = user['id']
        banned_until =  datetime.utcnow() + timedelta(minutes=ban_duration)
        
        # Update the banned_until field in the database
        

        flash(f'User {account_number} has been banned for {ban_duration} minutes.', 'success')
    else:
        flash('Account number not found.', 'danger')

    return redirect(url_for('admin'))

@app.route('/admin/unban', methods=['POST'])
def unban_user():
    if not session.get('is_admin'):
        flash('You are not authorized to unban users.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    account_number = request.form['account_number']

    cursor.execute("SELECT id FROM users WHERE account_number = ?", (account_number,))
    user = cursor.fetchone()

    if user:
        user_id = user['id']
        # Clear the banned_until field
        cursor.execute("UPDATE users SET banned_until = NULL WHERE id = ?", (user_id,))
        conn.commit()

        flash(f'User {account_number} has been unbanned.', 'success')
    else:
        flash('Account number not found.', 'danger')

    return redirect(url_for('admin'))
from datetime import datetime

@app.before_request
def check_user_restriction():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT banned_until, timeout_until FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        conn.close()

        if user:
            now = datetime.utcnow()
            banned_until = user['banned_until']
            timeout_until = user['timeout_until']

            # Convert banned_until to datetime if it exists
            if banned_until:
                try:
                    banned_until = datetime.strptime(banned_until, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    banned_until = datetime.strptime(banned_until, '%Y-%m-%d %H:%M:%S')

            # Convert timeout_until to datetime if it exists
            if timeout_until:
                try:
                    timeout_until = datetime.strptime(timeout_until, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    timeout_until = datetime.strptime(timeout_until, '%Y-%m-%d %H:%M:%S')

            # Redirect if banned
            if banned_until and now < banned_until:
                return redirect(url_for('banned'))

            # Show timeout page if in timeout
            if timeout_until and now < timeout_until:
                minutes_left = (timeout_until - now).seconds // 60
                return render_template('timeout.html', minutes_left=minutes_left)

    return None
from datetime import datetime
@app.route('/admin/lift_timeout/<int:user_id>', methods=['POST'])
def lift_timeout(user_id):
    if not session.get('is_admin'):
        flash('You are not authorized to perform this action.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Set timeout_until to NULL (or current time) to lift timeout
    cursor.execute('UPDATE users SET timeout_until = NULL WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('User\'s timeout has been lifted successfully.', 'success')
    return redirect(url_for('admin_users'))  # Redirect back to the admin users page
@app.route('/admin/edit_user', methods=['POST'])
  # Optional: If you have a decorator that limits to admin
def edit_user():
    account_number = request.form.get('account_number')
    new_username = request.form.get('new_username')
    new_email = request.form.get('new_email')
    new_account_number = request.form.get('new_account_number')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users SET username = ?, email = ?, account_number = ? WHERE account_number = ?
    ''', (new_username, new_email, new_account_number, account_number))

    conn.commit()
    conn.close()

    flash('User information updated successfully!', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/users')
def admin_users():
    if not session.get('is_admin'):
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id ,u.account_number, u.username, u.email, u.verified,
               b.neo, b.neons, b.neolites, u.is_banned, u.banned_until, u.timeout_until
        FROM users u
        LEFT JOIN balances b ON u.id = b.user_id
    ''')
    users = cursor.fetchall()
    conn.close()

    # Calculate the timeout status
    now = datetime.utcnow()

    updated_users = []  # List to store updated user information

    for user in users:
        # Convert sqlite3.Row to a dictionary to allow item assignment
        user_dict = dict(user)

        # Convert 'banned_until' to datetime if it exists
        if user_dict['banned_until']:
            try:
                banned_until = datetime.strptime(user_dict['banned_until'], '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                banned_until = datetime.strptime(user_dict['banned_until'], '%Y-%m-%d %H:%M:%S')  # Handle case without microseconds
        else:
            banned_until = None

        # Convert 'timeout_until' to datetime if it exists
        if user_dict['timeout_until']:
            try:
                timeout_until = datetime.strptime(user_dict['timeout_until'], '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                timeout_until = datetime.strptime(user_dict['timeout_until'], '%Y-%m-%d %H:%M:%S')  # Handle case without microseconds
        else:
            timeout_until = None

        # Check if the user is banned
        if user_dict['is_banned'] == 1 and (not banned_until or banned_until > now):
            user_dict['status'] = 'Banned'
        # Check if the user is timed out
        elif timeout_until and timeout_until > now:
            timeout_remaining = (timeout_until - now).seconds // 60
            user_dict['status'] = f'Timed Out ({timeout_remaining} min left)'
        else:
            user_dict['status'] = 'Active'

        updated_users.append(user_dict)  # Add the updated user data to the list

    return render_template('admin_users.html', users=updated_users)

@app.route('/convert', methods=['POST'])
def convert_currency():
    data = request.get_json()
    amount = float(data['amount'])
    from_coin = data['from']
    to_coin = data['to']
    user_id = session.get('user_id')

    if from_coin == to_coin:
        return jsonify({"success": False, "message": "Cannot convert to the same currency"})

    rates = {
        ('neo', 'neons'): 10,
        ('neo', 'neolites'): 100,
        ('neons', 'neo'): 0.1,
        ('neons', 'neolites'): 10,
        ('neolites', 'neo'): 0.01,
        ('neolites', 'neons'): 0.1
    }

    key = (from_coin, to_coin)
    if key not in rates:
        return jsonify({"success": False, "message": "Invalid conversion"})

    converted_amount = round(amount * rates[key], 2)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT neo, neons, neolites FROM balances WHERE user_id = ?", (user_id,))
    balances = cursor.fetchone()

    if not balances:
        conn.close()
        return jsonify({"success": False, "message": "Balance not found"})

    balance_map = {
        'neo': balances['neo'],
        'neons': balances['neons'],
        'neolites': balances['neolites']
    }

    if amount > balance_map[from_coin]:
        conn.close()
        return jsonify({"success": False, "message": "Insufficient funds"})

    balance_map[from_coin] -= amount
    balance_map[to_coin] += converted_amount

    cursor.execute("""
        UPDATE balances SET neo = ?, neons = ?, neolites = ? WHERE user_id = ?
    """, (balance_map['neo'], balance_map['neons'], balance_map['neolites'], user_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "converted": converted_amount})
@app.route('/all-transactions', methods=['GET'])
def all_transactions():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT t.*, u.username AS other_user
        FROM transactions t
        LEFT JOIN users u ON u.id = 
            CASE 
                WHEN t.sender_id = ? THEN t.receiver_id 
                ELSE t.sender_id 
            END
        WHERE t.sender_id = ? OR t.receiver_id = ?
        ORDER BY t.timestamp DESC
    ''', (user_id, user_id, user_id))

    transactions = cursor.fetchall()
    conn.close()

    return render_template('all-transactions.html', transactions=transactions)
@app.route('/admin/make_admin', methods=['POST'])
  # Optional: Use your admin required decorator if needed
def make_admin():
    account_number = request.form.get('account_number')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the user's role to admin
    cursor.execute('''
        UPDATE users SET role = 'admin' WHERE account_number = ?
    ''', (account_number,))

    conn.commit()
    conn.close()

    flash('User has been promoted to admin successfully!', 'info')
    return redirect(url_for('admin'))

@app.route('/receipt/<int:transaction_id>')
def receipt(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT t.*, u.account_number as receiver_acc
        FROM transactions t
        JOIN users u ON t.receiver_id = u.id
        WHERE t.id = ?
    ''', (transaction_id,))
    transaction = cursor.fetchone()

    conn.close()

    if not transaction:
        flash("Transaction not found.")
        return redirect(url_for('dashboard'))

    return render_template('receipt.html', transaction=transaction)



from flask import render_template, session, redirect, url_for, request, flash
import random
from datetime import datetime, timedelta

from flask import render_template, session, redirect, url_for, request, flash
import random
from datetime import datetime
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('neoncoin.db')
    conn.row_factory = sqlite3.Row
    return conn
def add_column_if_not_exists():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(balances);")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'spins_available' not in columns:
        print("fixing error ")
        cursor.execute("ALTER TABLE balances ADD COLUMN spins_available INTEGER DEFAULT 0;")
        print("error fixed")
        conn.commit()
    
    conn.close()
add_column_if_not_exists()
MAX_SPINS = 20
SPIN_COOLDOWN_MINUTES = 60

from datetime import datetime, timedelta, date



DAILY_BONUS_SPINS = 1
WEEKLY_BONUS_SPINS = 3

@app.route('/spin', methods=['GET', 'POST'])
def spin():
    if 'user_id' not in session:
        flash("You must be logged in to spin.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Get spin data
    c.execute("SELECT spins, last_spin FROM users WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    conn.close()

    if not user_data:
        flash("User not found.", "danger")
        return redirect(url_for('home'))

    spins, last_spin_str = user_data
    prize = None
    now = datetime.now()

    # Convert last spin to datetime
    last_spin = datetime.strptime(last_spin_str, '%Y-%m-%d %H:%M:%S') if last_spin_str else None

    # Time limit logic (optional)
    can_spin = True
    next_spin_time = None
    if last_spin:
        time_diff = now - last_spin
        if time_diff < timedelta(minutes=5):
            can_spin = False
            next_spin_time = (last_spin + timedelta(minutes=5)) - now

    if request.method == 'POST':
        if spins > 0 and can_spin:
            # 🎁 Random prize logic
            prizes = ['Neo', 'Neons', 'Neolites', 'Nothing']
            prize = random.choice(prizes)

            # Update user spins and last spin time
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("UPDATE users SET spins_available = spins_available - 1, last_spin = ? WHERE id = ?", (now.strftime('%Y-%m-%d %H:%M:%S'), user_id))
            conn.commit()
            conn.close()

            # flash or pass prize to show
            flash(f'You won: {prize}!', 'success')

            # You might want to record the prize in the DB too

            # Redirect to refresh values
            return redirect(url_for('spin'))
        else:
            flash("You can't spin right now.", "warning")

    # Re-fetch updated spin info
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT spins, last_spin FROM users WHERE id = ?", (user_id,))
    spins, last_spin_str = c.fetchone()
    conn.close()

    if last_spin_str:
        last_spin = datetime.strptime(last_spin_str, '%Y-%m-%d %H:%M:%S')
        time_remaining = timedelta(minutes=5) - (now - last_spin)
        if time_remaining.total_seconds() > 0:
            next_spin_time = time_remaining
        else:
            next_spin_time = None

    return render_template('spin.html', spins=spins, prize=prize, next_spin_time=next_spin_time)



def update_spin_availability(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure balances row exists
    cursor.execute('''
        INSERT INTO balances (user_id, neo, neons, neolites, spins_available, last_spin_update, daily_bonus_date, weekly_bonus_date)
        SELECT ?, 0, 0, 0, 0, NULL, NULL, NULL
        WHERE NOT EXISTS (SELECT 1 FROM balances WHERE user_id = ?)
    ''', (user_id, user_id))
    conn.commit()

    cursor.execute('SELECT spins_available, last_spin_update, daily_bonus_date, weekly_bonus_date FROM balances WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    spins = row['spins_available']
    last_update = row['last_spin_update']
    daily_bonus_date = row['daily_bonus_date']
    weekly_bonus_date = row['weekly_bonus_date']

    now = datetime.utcnow()

    # Refill based on time passed
    if last_update:
        try:
            last_update_dt = datetime.fromisoformat(last_update)
        except ValueError:
            last_update_dt = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S.%f')


        minutes_passed = (now - last_update_dt).total_seconds() // 60
        spins_to_add = int(minutes_passed // SPIN_COOLDOWN_MINUTES)

        if spins_to_add > 0:
            spins = min(MAX_SPINS, spins + spins_to_add)
            last_update_dt += timedelta(minutes=spins_to_add * SPIN_COOLDOWN_MINUTES)
            cursor.execute('UPDATE balances SET spins_available = ?, last_spin_update = ? WHERE user_id = ?',
                           (spins, last_update_dt, user_id))
            conn.commit()
    else:
        cursor.execute('UPDATE balances SET last_spin_update = ? WHERE user_id = ?', (now, user_id))
        conn.commit()

    # Daily bonus
    today = now.strftime('%Y-%m-%d')
    if daily_bonus_date != today:
        spins = min(MAX_SPINS, spins + DAILY_BONUS_SPINS)
        cursor.execute('UPDATE balances SET spins_available = ?, daily_bonus_date = ? WHERE user_id = ?',
                       (spins, today, user_id))
        conn.commit()

    # Weekly bonus
    this_week = now.strftime('%Y-%W')
    if weekly_bonus_date != this_week and now.weekday() == 0:
        spins = min(MAX_SPINS, spins + WEEKLY_BONUS_SPINS)
        cursor.execute('UPDATE balances SET spins_available = ?, weekly_bonus_date = ? WHERE user_id = ?',
                       (spins, this_week, user_id))
        conn.commit()

    # Determine time to next spin
    if last_update:
        next_spin_time = last_update_dt + timedelta(minutes=SPIN_COOLDOWN_MINUTES)
    else:
        next_spin_time = now + timedelta(minutes=SPIN_COOLDOWN_MINUTES)

    conn.close()
    return spins, next_spin_time


if __name__ == '__main__':
    app.run(debug=True)
