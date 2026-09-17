import sqlite3

def get_stages():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM palchi"
    cursor.execute(sql)

    stages = cursor.fetchall()
    conn.close()

    return stages

def add_stage(stage):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = "INSERT INTO palchi (nome_palco, descrizione, location, capienza, immagine1, immagine2, immagine3, tipologia) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    
    try:
        cursor.execute(sql, (stage['nome_palco'], stage['descrizione'], stage['location'], stage['capienza'], stage['immagine1'], stage['immagine2'], stage['immagine3'], stage['tipologia'],))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'inserimento del palco: {err}")
        conn.rollback()

    conn.commit()
    conn.close()

    return success

def get_stage_by_name(name):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM palchi WHERE nome_palco = ?"
    cursor.execute(sql, (name,))
    
    stage = cursor.fetchone()
    conn.close()

    return stage

def get_stage_by_id(id):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM palchi WHERE id = ?"
    cursor.execute(sql, (id,))
    
    nome_palco = cursor.fetchone()['nome_palco']
    conn.close()

    return nome_palco