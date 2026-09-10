import sqlite3
from werkzeug.security import generate_password_hash

def configurar_admin_oficial():
    conexao = sqlite3.connect('banco de dados.db')
    cursor = conexao.cursor()

    # Credenciais exatas fornecidas
    email_admin = 'bfdigital53@gmail.com'
    telefone_admin = '938058765'
    nova_pass = 'faustino2001@'
    
    pass_hash = generate_password_hash(nova_pass)

    try:
        # Garante que a tabela tem as colunas necessárias
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

        # Atualiza o registo do administrador com o e-mail, telefone e senha correta
        cursor.execute("""
            UPDATE usuarios 
            SET senha = ?, telefone = ?, tipo = 'admin' 
            WHERE email = ?
        """, (pass_hash, telefone_admin, email_admin))
        
        # Se o e-mail ainda não existir, cria o registo de raiz
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, telefone, senha, tipo) 
                VALUES (?, ?, ?, ?, ?)
            """, ('Administrador Principal', email_admin, telefone_admin, pass_hash, 'admin'))
            
        conexao.commit()
        print("Sucesso! Credenciais de administrador atualizadas com o telefone e pass corretos.")
        
    except Exception as e:
        print("Erro:", e)
    finally:
        conexao.close()

if __name__ == '__main__':
    configurar_admin_oficial()