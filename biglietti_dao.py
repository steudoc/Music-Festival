import sqlite3

def get_biglietti_by_user(user_id):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM biglietti WHERE utente = ?"
    cursor.execute(sql, (user_id,))
    biglietti = cursor.fetchone()

    cursor.close()
    conn.close()

    return biglietti

def add_ticket(ticket):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = "INSERT INTO biglietti (utente, type, Venerdì, Sabato, Domenica, data_acquisto) VALUES (?, ?, ?, ?, ?, ?)"
    
    try:
        cursor.execute(sql, (ticket['utente'], ticket['type'], ticket['Venerdì'], ticket['Sabato'], ticket['Domenica'], ticket['data_acquisto'],))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'inserimento del biglietto: {err}")
        conn.rollback()

    cursor.close()
    conn.close()

    return success

def get_stats_per_day(day):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = f"SELECT COUNT(*) as n FROM biglietti WHERE [{day}] = ?"
    cursor.execute(sql, (1,))
    n = cursor.fetchone()["n"]

    cursor.close()
    conn.close()

    return n

def get_stats_per_type(type):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = f"SELECT COUNT(*) as n FROM biglietti WHERE type = ?"
    cursor.execute(sql, (type,))
    n = cursor.fetchone()["n"]

    cursor.close()
    conn.close()

    return n