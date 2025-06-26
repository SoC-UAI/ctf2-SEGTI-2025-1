from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'ctf-secret'
DB = 'database.db'

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("CREATE TABLE users (username TEXT, password TEXT)")
        c.execute("INSERT INTO users VALUES ('admin', 'supersecure')")
        c.execute("INSERT INTO users VALUES ('user', '1234')")

        c.execute("CREATE TABLE flags (id INTEGER PRIMARY KEY, flag TEXT)")
        c.execute("INSERT INTO flags (flag) VALUES ('segti{SQL_injEcTeD}')")

        c.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT)")
        conn.commit()
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    sqli_flag = ""
    resultado = []
    query_mostrada = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        try:
            query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
            print("Consulta ejecutada:", query)
            query_mostrada = query
            result = c.execute(query).fetchall()
            flag_row = c.execute("SELECT flag FROM flags").fetchone()
        except Exception as e:
            return f"Error en la consulta: {str(e)}"

        conn.close()

        # Mostrar FLAG SOLO si se usa exactamente: ' OR '1'='1
        if "' OR '1'='1" in username or "' OR '1'='1" in password:
            sqli_flag = flag_row[0]

        if result:
            resultado = [dict(row) for row in result]

        # Login real (sin SQLi)
        if username.strip() == 'admin' and password.strip() == 'supersecure':
            session['user'] = 'admin'
            return redirect('/message-board')

    return render_template('login.html', flag=sqli_flag, resultado=resultado, consulta=query_mostrada)

@app.route('/message-board', methods=['GET', 'POST'])
def message_board():
    if session.get('user') != 'admin':
        return redirect('/login')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Limpieza automática de mensajes al entrar
    if request.method == 'GET':
        c.execute("DELETE FROM messages")
        conn.commit()

    flag_to_display = ""

    if request.method == 'POST':
        msg = request.form['msg']
        c.execute("INSERT INTO messages (content) VALUES (?)", (msg,))
        conn.commit()

        if msg.strip() == '<script>alert("XSS")</script>':
            flag_to_display = "segti{XSS_aLerT}"

    c.execute("SELECT content FROM messages")
    msgs = c.fetchall()
    conn.close()

    return render_template('message_board.html', messages=msgs, flag=flag_to_display)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0")
