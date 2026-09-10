import sqlite3
from werkzeug.security import generate_password_hash

# Liga à base de dados local
conexao = sqlite3.connect('banco de dados.db')
cursor = conexao.cursor()

# Força a criação do admin com dados limpos e senha encriptada
email = 'bfdigital53@gmail.com'
telefone = '938058765'
senha_hash = generate_password_hash('Faustino2001@')

# Apaga qualquer registo antigo com este email para evitar duplicados
cursor.execute("DELETE FROM usuarios WHERE email = ?", (email,))

# Insere o admin oficial correto
cursor.execute("""
    INSERT INTO usuarios (nome, email, telefone, senha, tipo) 
    VALUES (?, ?, ?, ?, ?)
""", ('Administrador', email, telefone, senha_hash, 'admin'))

conexao.commit()
conexao.close()

print("Utilizador administrador recriado com sucesso!")