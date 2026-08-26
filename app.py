import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash, send_from_directory
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bf_digital_exchange_global_key_2026')
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'bfdigital53@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'Faustino2001@')
app.config['MAIL_DEFAULT_SENDER'] = ('BF Digital Exchange', 'bfdigital53@gmail.com')

mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefone TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            iban TEXT DEFAULT 'N/A',
            foto TEXT DEFAULT 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            par TEXT UNIQUE NOT NULL,
            compra REAL NOT NULL,
            venda REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            usuario TEXT NOT NULL,
            texto TEXT NOT NULL,
            tipo TEXT DEFAULT 'texto',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO exchange_rates (par, compra, venda) VALUES ('EUR = AOA', 1300.0, 1320.0)")
    cursor.execute("INSERT OR IGNORE INTO exchange_rates (par, compra, venda) VALUES ('USD = AOA', 1200.0, 1220.0)")
    
    cursor.execute("SELECT * FROM users WHERE email = 'bfdigital53@gmail.com'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (nome, email, telefone, data_nascimento, password, is_admin, status) VALUES (?, ?, ?, '1990-01-01', 'admin123', 1, 'Aprovado')",
                       ('Paulo Chende-Kumbi (Admin Principal)', 'bfdigital53@gmail.com', '+244900000001'))
            
    conn.commit()
    conn.close()

init_db()

APPROVAL_TEMPLATE = '''
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #030712; padding: 30px; border-radius: 12px; color: #f8fafc;">
    <div style="text-align: center; border-bottom: 1px solid #1e293b; padding-bottom: 20px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #facc15; letter-spacing: 2px;">BF DIGITAL EXCHANGE</h2>
        <p style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px;">Global Financial Services & Exchange</p>
    </div>
    <div>
        <p style="font-size: 16px;"><strong>Olá, {{ nome }},</strong></p>
        <p style="color: #cbd5e1; line-height: 1.6;">A sua conta na <strong>BF Digital Exchange</strong> foi validada e <strong style="color: #22c55e;">aprovada</strong> com sucesso pela administração global.</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="http://127.0.0.1:5000/" style="background: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600;">Aceder à Plataforma</a>
        </p>
    </div>
</div>
'''

REJECT_TEMPLATE = '''
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #030712; padding: 30px; border-radius: 12px; color: #f8fafc;">
    <div style="text-align: center; border-bottom: 1px solid #1e293b; padding-bottom: 20px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #facc15; letter-spacing: 2px;">BF DIGITAL EXCHANGE</h2>
        <p style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px;">Global Financial Services & Exchange</p>
    </div>
    <div>
        <p style="font-size: 16px;"><strong>Olá, {{ nome }},</strong></p>
        <p style="color: #cbd5e1; line-height: 1.6;">O seu pedido de registo na <strong>BF Digital Exchange</strong> foi <strong style="color: #ef4444;">negado / não aprovado</strong> neste momento.</p>
        <p style="color: #cbd5e1;">Para esclarecimentos, contacte o suporte global.</p>
    </div>
</div>
'''

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT par, compra, venda FROM exchange_rates")
    rates = cursor.fetchall()
    conn.close()
    return render_template('index.html', rates=rates)

@app.route('/register', methods=['POST'])
def register():
    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form['telefone']
    data_nascimento_str = request.form['data_nascimento']
    password = request.form['password']
    
    try:
        data_nasc = datetime.strptime(data_nascimento_str, '%Y-%m-%d')
        hoje = datetime.now()
        idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
        if idade < 18:
            flash("Erro: Requer idade mínima de 18 anos.", "danger")
            return redirect(url_for('index'))
    except Exception:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for('index'))
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (nome, email, telefone, data_nascimento, password, status) VALUES (?, ?, ?, ?, ?, 'Pendente')",
                       (nome, email, telefone, data_nascimento_str, password))
        conn.commit()
        conn.close()
        
        try:
            msg_admin = Message(f"[NOVO REGISTO GLOBAL] Cliente: {nome}", recipients=['bfdigital53@gmail.com'])
            msg_admin.body = f"Novo registo submetido na BF Digital Exchange:\n\nNome: {nome}\nE-mail: {email}\nTelefone: {telefone}\n\nAceda ao painel administrativo global para aprovar ou recusar."
            mail.send(msg_admin)
        except Exception:
            pass

        flash("Registo submetido com sucesso! A administração foi notificada.", "success")
    except Exception:
        flash("Este e-mail já se encontra registado.", "danger")
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    telefone = request.form['telefone']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND telefone = ? AND password = ?", (email, telefone, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        if user[8] != 1 and user[9] != 'Aprovado':
            flash("A sua conta encontra-se pendente de aprovação.", "warning")
            return redirect(url_for('index'))
            
        session['user_id'] = user[0]
        session['nome'] = user[1]
        session['email'] = user[2]
        session['foto'] = user[6]
        session['is_admin'] = user[8]
        flash("Sessão iniciada com sucesso.", "success")
        if user[8] == 1:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    else:
        flash("Credenciais inválidas.", "danger")
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin') == 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT par, compra, venda FROM exchange_rates")
    rates = cursor.fetchall()
    cursor.execute("SELECT id, nome, email, telefone, foto, status FROM users WHERE is_admin = 1")
    admins = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', rates=rates, admins=admins, nome=session['nome'], foto=session.get('foto'), user_id=session['user_id'])

@app.route('/chat/<int:admin_id>')
def chat_room(admin_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, foto FROM users WHERE id = ? AND is_admin = 1", (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    if not admin:
        flash("Administrador não encontrado.", "danger")
        return redirect(url_for('dashboard'))
    
    room = f"room_{admin_id}_{session['user_id']}"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, texto, timestamp FROM messages WHERE room = ? ORDER BY id ASC", (room,))
    history = cursor.fetchall()
    conn.close()

    return render_template('chat.html', admin=admin, nome=session['nome'], foto=session.get('foto'), history=history, room=room, user_id=session['user_id'])

@app.route('/admin_chats')
def admin_chats():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, foto FROM users WHERE is_admin = 0")
    clients = cursor.fetchall()
    conn.close()
    return render_template('admin_chats.html', clients=clients, admin_name=session['nome'], admin_id=session['user_id'])

@app.route('/admin_chat_room/<int:client_id>')
def admin_chat_room(client_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, foto FROM users WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    conn.close()
    if not client:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for('admin_chats'))
    
    room = f"room_{session['user_id']}_{client_id}"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, texto, timestamp FROM messages WHERE room = ? ORDER BY id ASC", (room,))
    history = cursor.fetchall()
    conn.close()

    return render_template('admin_chat_room.html', client=client, admin_name=session['nome'], admin_id=session['user_id'], history=history, room=room)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'user_id' not in session:
        return {'success': False}, 403
    if 'file' not in request.files:
        return {'success': False}, 400
    file = request.files['file']
    if file.filename == '':
        return {'success': False}, 400
    if file and file.filename.endswith('.pdf'):
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return {'success': True, 'url': url_for('download_file', name=filename), 'filename': filename}
    return {'success': False}, 400

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], name)

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT par, compra, venda FROM exchange_rates")
    rates = cursor.fetchall()
    cursor.execute("SELECT id, nome, email, telefone, data_nascimento, status, is_admin, password FROM users")
    users = cursor.fetchall()
    conn.close()
    
    is_main_admin = (session.get('email') == 'bfdigital53@gmail.com')
    return render_template('admin.html', rates=rates, users=users, admin_id=session['user_id'], is_main_admin=is_main_admin)

@app.route('/create_admin', methods=['POST'])
def create_admin():
    if 'user_id' not in session or session.get('email') != 'bfdigital53@gmail.com':
        flash("Acesso negado: Apenas o Administrador Principal pode criar novos gestores.", "danger")
        return redirect(url_for('admin_panel'))
        
    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form['telefone']
    password = request.form['password']
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (nome, email, telefone, data_nascimento, password, is_admin, status) VALUES (?, ?, ?, '1990-01-01', ?, 1, 'Aprovado')",
                       (nome, email, telefone, password))
        conn.commit()
        conn.close()
        flash("Novo gestor criado com sucesso pelo Administrador Principal!", "success")
    except Exception:
        flash("Erro: Este e-mail já está registado.", "danger")
    return redirect(url_for('admin_panel'))

@app.route('/update_rates', methods=['POST'])
def update_rates():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    par = request.form['par']
    compra = float(request.form['compra'])
    venda = float(request.form['venda'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE exchange_rates SET compra = ?, venda = ? WHERE par = ?", (compra, venda, par))
    conn.commit()
    conn.close()
    flash(f"Tabelas de cotações para {par} atualizadas com sucesso!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/approve_user/<int:user_id>')
def approve_user(user_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome, email FROM users WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    if u:
        cursor.execute("UPDATE users SET status = 'Aprovado' WHERE id = ?", (user_id,))
        conn.commit()
        try:
            msg = Message("Conta Aprovada - BF Digital Exchange", recipients=[u[1]])
            msg.html = render_template_string(APPROVAL_TEMPLATE, nome=u[0])
            mail.send(msg)
        except Exception:
            pass
    conn.close()
    flash("Conta aprovada e e-mail enviado ao cliente.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/reject_user/<int:user_id>')
def reject_user(user_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome, email FROM users WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    if u:
        cursor.execute("UPDATE users SET status = 'Negado' WHERE id = ?", (user_id,))
        conn.commit()
        try:
            msg = Message("Estado do Registo - BF Digital Exchange", recipients=[u[1]])
            msg.html = render_template_string(REJECT_TEMPLATE, nome=u[0])
            mail.send(msg)
        except Exception:
            pass
    conn.close()
    flash("Registo negado e cliente notificado por e-mail.", "warning")
    return redirect(url_for('admin_panel'))

@app.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form['telefone']
    status = request.form['status']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET nome = ?, email = ?, telefone = ?, status = ?, password = ? WHERE id = ?", (nome, email, telefone, status, password, user_id))
    conn.commit()
    conn.close()
    flash("Dados atualizados com sucesso.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/notify_user/<int:user_id>', methods=['POST'])
def notify_user(user_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    assunto = request.form['assunto']
    mensagem = request.form['mensagem']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome, email FROM users WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    conn.close()
    
    if u:
        try:
            msg = Message(assunto, recipients=[u[1]])
            msg.body = f"Olá {u[0]},\n\n{mensagem}\n\nAtentamente,\nEquipa BF Digital Exchange."
            mail.send(msg)
            flash(f"Notificação enviada por e-mail para {u[1]} com sucesso.", "success")
        except Exception:
            flash("Erro ao enviar e-mail.", "danger")
    return redirect(url_for('admin_panel'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('index'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ? AND is_admin = 0", (user_id,))
    conn.commit()
    conn.close()
    flash("Registo eliminado.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        email = request.form['email']
        telefone = request.form['telefone']
        nova_password = request.form['nova_password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ? AND telefone = ?", (nova_password, email, telefone))
        conn.commit()
        rows = cursor.rowcount
        conn.close()
        
        if rows > 0:
            flash("Palavra-passe alterada com sucesso.", "success")
            return redirect(url_for('index'))
        else:
            flash("Dados não encontrados.", "danger")
    return render_template('recover.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sessão terminada.", "info")
    return redirect(url_for('index'))

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    usuario = data['usuario']
    texto = data['texto']
    tipo = data.get('tipo', 'texto')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (room, usuario, texto, tipo) VALUES (?, ?, ?, ?)", (room, usuario, texto, tipo))
    conn.commit()
    conn.close()

    emit('receive_message', data, room=room)
    emit('global_notification', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)