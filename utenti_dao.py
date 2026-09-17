import sqlite3

def get_user_by_id(user_id):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM utenti WHERE id = ?"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

def get_user_by_email(email):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM utenti WHERE email = ?"
    cursor.execute(sql, (email,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

def add_user(user):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = "INSERT INTO utenti (email, password, nome, cognome, organizzatore, data_registrazione, sesso) VALUES (?, ?, ?, ?, ?, ?, ?)"
    
    try:
        cursor.execute(sql, (user['email'], user['password'], user['nome'], user['cognome'], user['organizzatore'], user['data_registrazione'], user['sesso'],))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'inserimento dell'utente: {err}")
        conn.rollback()

    cursor.close()
    conn.close()

    return success