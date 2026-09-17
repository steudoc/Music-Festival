import sqlite3
from datetime import datetime, timedelta

def calcola_ora_fine(ora_inizio, durata_minuti):
    dt_inizio = datetime.strptime(ora_inizio, "%H:%M")
    dt_fine = dt_inizio + timedelta(minutes=int(durata_minuti))
    return dt_fine.strftime("%H:%M")

def get_performance_list(active):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE performance.visibile = ?
        ORDER BY
            CASE performance.giorno
                WHEN 'Venerdì' THEN 1
                WHEN 'Sabato' THEN 2
                WHEN 'Domenica' THEN 3
                ELSE 4
            END,
            performance.ora ASC
    """
    cursor.execute(sql, (active,))
    performances = cursor.fetchall()

    cursor.close()
    conn.close()

    performances_with_end = []
    for perf in performances:
        perf = dict(perf)  # se è un Row, converti in dict
        perf['ora_fine'] = calcola_ora_fine(perf['ora'], perf['durata'])
        performances_with_end.append(perf)

    return performances_with_end

def get_performance_homepage():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE performance.visibile = ? AND performance.homepage = ?
        ORDER BY
            CASE performance.giorno
                WHEN 'Venerdì' THEN 1
                WHEN 'Sabato' THEN 2
                WHEN 'Domenica' THEN 3
                ELSE 4
            END,
            performance.ora ASC
    """
    cursor.execute(sql, (1, 1,))
    performances = cursor.fetchall()

    cursor.close()
    conn.close()

    return performances

def get_performance_by_artist(artist):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE LOWER(artista) = LOWER(?) AND visibile = 1
    """
    cursor.execute(sql, (artist,))
    performances = cursor.fetchone()

    cursor.close()
    conn.close()

    return performances

def get_performance_by_id(performance_id):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE performance.id = ?
    """
    cursor.execute(sql, (performance_id,))
    performance = cursor.fetchone()

    cursor.close()
    conn.close()

    return performance

def get_performances_by_organizer(organizer_id):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE organizzatore = ? AND visibile = 1
    """
    cursor.execute(sql, (organizer_id,))
    performances = cursor.fetchall()

    cursor.close()
    conn.close()

    return performances

def get_draft_by_organizer(organizer_id):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE organizzatore = ? AND visibile = 0
    """
    cursor.execute(sql, (organizer_id,))
    drafts = cursor.fetchall()

    cursor.close()
    conn.close()

    return drafts

def add_performance(performance):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = "INSERT INTO performance (artista, giorno, ora, durata, descrizione, palco, genere, immagine1, visibile, organizzatore, immagine2, immagine3, homepage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    
    try:
        cursor.execute(sql, (performance['artista'], performance['giorno'], performance['ora'], performance['durata'], performance['descrizione'], performance['palco'], performance['genere'], performance['immagine1'], performance['visibile'], performance['organizzatore'], performance['immagine2'], performance['immagine3'], performance['homepage'],))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'inserimento della performance: {err}")
        conn.rollback()

    cursor.close()
    conn.close()

    return success

def check_performance_overlaps(giorno, palco):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM performance WHERE giorno = ? AND palco = ? AND visibile = 1"
    cursor.execute(sql, (giorno, palco))
    overlaps = cursor.fetchall()

    cursor.close()
    conn.close()

    return overlaps

def update_performance(performance):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = "UPDATE performance SET artista = ?, giorno = ?, ora = ?, durata = ?, descrizione = ?, palco = ?, genere = ?, immagine1 = ?, immagine2 = ?, immagine3 = ?, visibile = ? WHERE id = ?"
    
    try:
        cursor.execute(sql, (performance['artista'], performance['giorno'], performance['ora'], performance['durata'], performance['descrizione'], performance['palco'], performance['genere'], performance['immagine1'], performance['immagine2'], performance['immagine3'], performance['visibile'], performance['id']))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'aggiornamento della performance: {err}")
        conn.rollback()

    cursor.close()
    conn.close()

    return success

def delete_performance(performance_id):
    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()

    success = False
    sql = "DELETE FROM performance WHERE id = ?"
    
    try:
        cursor.execute(sql, (performance_id,))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'eliminazione della performance: {err}")
        conn.rollback()

    cursor.close()
    conn.close()

    return success

def set_homepage_performances(id_list):
    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()

    success = False
    
    try:
        sql = "UPDATE performance SET homepage = 0"
        cursor.execute(sql)
        conn.commit()
        sql = "UPDATE performance SET homepage = ? WHERE id = ?"
        for performance_id in id_list:
            cursor.execute(sql, (1, performance_id,))
        conn.commit()
        success = True
    except Exception as err:
        print(f"Errore durante l'aggiornamento della homepage: {err}")
        conn.rollback()
        success = False

    cursor.close()
    conn.close()

    return success

def filter_performances(giorno=None, palco=None, genere=None):
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT performance.*, palchi.nome_palco AS nome_palco
        FROM performance
        JOIN palchi ON performance.palco = palchi.id
        WHERE performance.visibile = 1
    """
    params = []

    if giorno:
        sql += " AND performance.giorno = ?"
        params.append(giorno)
    if palco:
        sql += " AND performance.palco = ?"
        params.append(palco)
    if genere:
        sql += " AND LOWER(performance.genere) LIKE LOWER(?)"
        params.append(f"%{genere}%")

    sql += """
        ORDER BY
            CASE performance.giorno
                WHEN 'Venerdì' THEN 1
                WHEN 'Sabato' THEN 2
                WHEN 'Domenica' THEN 3
                ELSE 4
            END,
            performance.ora ASC
    """

    cursor.execute(sql, params)
    performances = cursor.fetchall()
    cursor.close()
    conn.close()

    performances_with_end = []
    for perf in performances:
        perf_dict = dict(perf)
        perf_dict['ora_fine'] = calcola_ora_fine(perf_dict['ora'], perf_dict['durata'])
        performances_with_end.append(perf_dict)

    return performances_with_end