import sqlite3
from werkzeug.security import generate_password_hash

def configurar_admin():
    # Liga à base de dados (ajusta o nome do ficheiro se necessário, ex: banco de dados.db ou bf_exchange.db)
    conexao = sqlite3.connect('banco de dados.db')
    cursor = conexao.cursor()

    # Dados definitivos do administrador
    email_admin = 'bfdigital53@gmail.com'
    telefone_admin = '938058765'
    nova_pass = 'faustino2001@'
    
    # Encriptação segura da palavra-passe com Werkzeug
    pass_hash = generate_password_hash(nova_pass)

    try:
        # Garante que a tabela de utilizadores existe (ajusta se a tua estrutura for diferente)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT UNIQUE,
                telefone TEXT,
                senha TEXT,
                tipo TEXT
            )
        """)

        # Tenta atualizar caso o e-mail já exista
        cursor.execute("""
            UPDATE usuarios 
            SET senha = ?, telefone = ?, tipo = 'admin' 
            WHERE email = ?
        """, (pass_hash, telefone_admin, email_admin))
        
        # Se o e-mail ainda não existir, insere um novo registo
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, telefone, senha, tipo) 
                VALUES (?, ?, ?, ?, ?)
            """, ('Administrador Principal', email_admin, telefone_admin, pass_hash, 'admin'))
            
        conexao.commit()
        print("Sucesso! As credenciais encriptadas do administrador foram aplicadas.")
        print(f"E-mail: {email_admin}")
        print(f"Telefone: {telefone_admin}")
        print(f"Palavra-passe: {nova_pass}")
        print(f"Hash gerada: {pass_hash}")
        
    except Exception as e:
        print("Ocorreu um erro ao atualizar a base de dados:", e)
    finally:
        conexao.close()

if __name__ == '__main__':
    configurar_admin()