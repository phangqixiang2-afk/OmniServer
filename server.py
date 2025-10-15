from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this later

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect('iot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature REAL,
                    humidity REAL,
                    gas REAL,
                    dust REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('iot_data.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists!"
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('iot_data.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('iot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return render_template('dashboard.html', username=session['user'], data=rows)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_data():
    data = request.get_json()
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    gas = data.get('gas')
    dust = data.get('dust')
    conn = sqlite3.connect('iot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO data (temperature, humidity, gas, dust) VALUES (?, ?, ?, ?)",
              (temperature, humidity, gas, dust))
    conn.commit()
    conn.close()
    return {"message": "Data saved success", "status": "ok"}

@app.route('/latest')
def latest_data():
    conn = sqlite3.connect('iot_data.db')
    c = conn.cursor()
    c.execute("SELECT temperature, humidity, gas, dust, timestamp FROM data ORDER BY timestamp DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return {"data": rows}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
