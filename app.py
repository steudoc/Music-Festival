from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta

from models import User
from PIL import Image

PROFILE_IMG_HEIGHT = 2000
POST_IMG_WIDTH = 2000

import utenti_dao, performance_dao, biglietti_dao, palchi_dao

app = Flask(__name__)
app.config['SECRET_KEY'] = 'misunpiemunteis'

login_manager = LoginManager()
login_manager.init_app(app)

# Configure the login manager
@login_manager.user_loader
def load_user(user_id):
    db_user = utenti_dao.get_user_by_id(user_id)

    if db_user is not None:
        user = User(id = db_user['id'],
                    email = db_user['email'],
                    password = db_user['password'],
                    nome = db_user['nome'],
                    cognome = db_user['cognome'],
                    organizzatore = db_user['organizzatore'],
                    data_registrazione = db_user['data_registrazione'],
                    sesso = db_user['sesso'])
    else:
        user = None

    return user

# Route to view the login page
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    if email == '':
        flash('Devi inserire un indirizzo email', 'danger')
        return redirect(url_for('register'))
    if password == '':
        flash('Devi inserire una password', 'danger')
        return redirect(url_for('register'))

    db_user = utenti_dao.get_user_by_email(email)
    if db_user and check_password_hash(db_user['password'], password):
        user = User(id=db_user['id'],
                    email=db_user['email'],
                    password=db_user['password'],
                    nome=db_user['nome'],
                    cognome=db_user['cognome'],
                    organizzatore=db_user['organizzatore'],
                    data_registrazione=db_user['data_registrazione'],
                    sesso = db_user['sesso'])
        login_user(user)
        if current_user.sesso == 'M':
            flash("Bentornato " + db_user["nome"] + "! Ti stavamo aspettando!", "success")
        elif current_user.sesso == 'F':
            flash("Bentornata " + db_user["nome"] + "! Ti stavamo aspettando!", "success")
        else:
            flash("Bentornat* " + db_user["nome"] + "! Ti stavamo aspettando!", "success")
        return redirect(url_for('home'))
    else:
        flash('Email o password errati', 'danger')
        return redirect(url_for('home'))

# Route to view the login page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Route to view the registration page
@app.route('/register')
def register():
    return render_template('register.html')

# Route to register a new user
@app.route('/register_user', methods=['POST'])
def register_user():
    new_user = request.form.to_dict()

    if new_user['email'] == '':
        flash('Devi inserire un indirizzo email', 'danger')
        return redirect(url_for('register'))
    if new_user['password'] == '':
        flash('Devi inserire una password', 'danger')
        return redirect(url_for('register'))
    if new_user['nome'] == '' or new_user['cognome'] == '':
        flash('Devi inserire nome e cognome', 'danger')
        return redirect(url_for('register'))
    if new_user['sesso'] == '':
        flash('Devi indicare il sesso', 'danger')
        return redirect(url_for('register'))

    user_in_db = utenti_dao.get_user_by_email(new_user['email'])
    if user_in_db is not None:
        flash('Indirizzo email già registrato', 'danger')
        return redirect(url_for('register'))
    else:
        new_user['password'] = generate_password_hash(new_user['password'])
        new_user['data_registrazione'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success = utenti_dao.add_user(new_user)
        if success:
            db_user = utenti_dao.get_user_by_email(new_user['email'])
            flash('Registrazione avvenuta con successo!', 'success')
            user = User(id=db_user['id'],
                    email=db_user['email'],
                    password=db_user['password'],
                    nome=db_user['nome'],
                    cognome=db_user['cognome'],
                    organizzatore=db_user['organizzatore'],
                    data_registrazione=db_user['data_registrazione'],
                    sesso = db_user['sesso'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Errore durante la registrazione, riprova', 'danger')
            
    return redirect(url_for('register'))    

# Route to view the home page
@app.route('/')
def home():
    db_performances = performance_dao.get_performance_homepage()
    return render_template('home.html', p_spettacoli=db_performances)

# Route to view the about us page
@app.route('/about')
def about():
    return render_template('about.html')

# Route to view dashboard for organizers
@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    if user.organizzatore:
        db_performances = performance_dao.get_performance_list(True)
        db_my_performances = performance_dao.get_performances_by_organizer(user.id)
        db_draft_rows = performance_dao.get_draft_by_organizer(user.id)
        db_draft = []
        for draft_row in db_draft_rows:
            draft = dict(draft_row)
            draft['can_publish'] = check_overlaps(draft)
            db_draft.append(draft)
        return render_template('dashboard.html', p_performances=db_performances, p_my_performances=db_my_performances, p_draft=db_draft)
    else:
        flash('Accesso non autorizzato alla dashboard', 'danger')
        return redirect(url_for('home'))

# Route to view new performance creation page   
@app.route('/dashboard/nuova_performance')
@login_required
def nuova_performance():
    user = current_user
    if user.organizzatore:
        db_performances = performance_dao.get_performance_list(True)
        db_stages = palchi_dao.get_stages()
        return render_template('nuova_performance.html', p_performances=db_performances, p_stages=db_stages)
    else:
        flash('Accesso non autorizzato alla creazione di una nuova performance', 'danger')
        return redirect(url_for('home'))

# Route to create a new performance    
@app.route('/dashboard/performance/create', methods=['POST'])
@login_required
def create_performance():
    azione = request.form.get('azione')
    performance_data = request.form.to_dict()

    if performance_data['artista'] == '' or performance_data['giorno'] == '' or performance_data['ora'] == '' or performance_data['durata'] == '' or performance_data['descrizione'] == '' or performance_data['palco'] == '' or performance_data['genere'] == '':
        flash('Tutti i campi sono obbligatori', 'danger')
        return redirect(url_for('nuova_performance'))
    
    if "T" in performance_data["ora"]:
        performance_data["ora"] = performance_data["ora"].replace("T", " ") + ":00"

    performance_data['organizzatore'] = current_user.id
    
    image_fields = ['immagine1', 'immagine2', 'immagine3']
    for idx, field in enumerate(image_fields, start=1):
        img_file = request.files.get(field)
        img_save = None
        if img_file and img_file.filename:
            img = Image.open(img_file)

            # Trova il lato minore per ottenere un quadrato
            min_side = min(img.size)

            # Calcola le coordinate per il crop centrale
            left = (img.width - min_side) / 2
            top = (img.height - min_side) / 2
            right = left + min_side
            bottom = top + min_side

            # Ritaglia il quadrato centrale
            img = img.crop((left, top, right, bottom))

            # Utilize the artist's name and index for unique image filenames
            ext = img_file.filename.split('.')[-1]
            img_filename = f"uploads/{performance_data.get('artista').lower()}_{idx}_{str(datetime.now().timestamp())}.{ext}"
            img.save(f"static/{img_filename}")
            img_save = img_filename

        performance_data[field] = img_save if img_file and img_file.filename else None

    if performance_data.get('homepage') == 'on':
        performance_data['homepage'] = 1
    else:
        performance_data['homepage'] = 0

    performance_in_db = performance_dao.get_performance_by_artist(performance_data['artista'])
    if performance_in_db:
        flash('Esiste già una performance pubblicata con questo artista', 'danger')
        return render_template('nuova_performance.html',
            p_stages = palchi_dao.get_stages(),
            p_performances = performance_dao.get_performance_list(True), 
            form_data=performance_data
        )
    else:
        if check_overlaps(performance_data): 
            if azione == 'bozza':
                performance_data['visibile'] = False
            elif azione == 'pubblica':
                performance_data['visibile'] = True
            else:
                flash('Azione non valida', 'danger')
                return redirect(url_for('nuova_performance'))
                  
            success = performance_dao.add_performance(performance_data)
            if success:
                if azione == 'bozza':
                    flash('Bozza salvata con successo!', 'success')
                else:
                    flash('Performance pubblicata con successo!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Errore durante il salvataggio della performance, riprova', 'danger')
        else:
            flash(f"Il palco selezionato è già occupato {performance_data['giorno']} alle {performance_data['ora']}", 'danger')
            return render_template('nuova_performance.html',
                p_stages = palchi_dao.get_stages(),
                p_performances = performance_dao.get_performance_list(True),
                form_data=performance_data
            )
    
    return redirect(url_for('nuova_performance'))

@app.route('/draft/modify', methods=['POST'])
@login_required
def modify_draft():
    performance_form = request.form.to_dict()
    db_performance = dict(performance_dao.get_performance_by_id(performance_form['id']))

    if performance_form['artista'] != '':
        db_performance['artista'] = performance_form['artista']
    if performance_form.get('giorno', '') != '':
        db_performance['giorno'] = performance_form['giorno']
    if performance_form['ora'] != '':
        if "T" in performance_form["ora"]:
            db_performance['ora'] = performance_form['ora'].replace("T", " ") + ":00"
        else:
            db_performance['ora'] = performance_form['ora']
    if performance_form['durata'] != '':
        db_performance['durata'] = performance_form['durata']
    if performance_form['descrizione'] != '':
        db_performance['descrizione'] = performance_form['descrizione']
    if performance_form.get('palco', '') != '':
        db_performance['palco'] = performance_form['palco']
    if performance_form['genere'] != '':
        db_performance['genere'] = performance_form['genere']
    image_fields = ['immagine1', 'immagine2', 'immagine3']
    for idx, field in enumerate(image_fields, start=1):
        img_file = request.files.get(field)
        if img_file and img_file.filename:
            img = Image.open(img_file)

            # Trova il lato minore per ottenere un quadrato
            min_side = min(img.size)

            # Calcola le coordinate per il crop centrale
            left = (img.width - min_side) / 2
            top = (img.height - min_side) / 2
            right = left + min_side
            bottom = top + min_side

            # Ritaglia il quadrato centrale
            img = img.crop((left, top, right, bottom))

            # Utilize the artist's name and index for unique image filenames
            ext = img_file.filename.split('.')[-1]
            img_filename = f"uploads/{db_performance.get('artista').lower()}_{idx}_{str(datetime.now().timestamp())}.{ext}"
            img.save(f"static/{img_filename}")
            img_save = img_filename
            db_performance[field] = img_save if img_file and img_file.filename else None
        else:
             # Se non viene caricata una nuova immagine, mantieni quella vecchia
            db_performance[field] = db_performance.get(field)
    
    azione = request.form.get('azione')
    performance_in_db = performance_dao.get_performance_by_artist(db_performance['artista'])
    if performance_in_db:
        flash('Esiste già una performance pubblicata con questo artista', 'danger')
    else:
        if check_overlaps(db_performance): 
            if azione == 'bozza':
                db_performance['visibile'] = False
            elif azione == 'pubblica':
                db_performance['visibile'] = True
            else:
                flash('Azione non valida', 'danger')
                return redirect(url_for('modifica_bozza', id=db_performance['id']))
                  
            success = performance_dao.update_performance(db_performance)
            if success:
                if azione == 'bozza':
                    flash('Bozza salvata con successo!', 'success')
                else:
                    flash('Performance pubblicata con successo!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Errore durante il salvataggio della performance, riprova', 'danger')
        else: 
            flash('Il palco selezionato è già occupato in quella fascia oraria!', 'danger')

    return redirect(url_for('modifica_bozza', id=db_performance['id']))

# Function to check for overlapping performances
def check_overlaps(performance):
    overlap = performance_dao.check_performance_overlaps(performance['giorno'], performance['palco'])
    if overlap is not None:
        for perf in overlap:
            if (perf['ora'] == performance['ora']) or \
               (perf['ora'] < performance['ora'] < sum_minutes(perf['ora'], perf['durata'])) or \
               (performance['ora'] < perf['ora'] < sum_minutes(performance['ora'], performance['durata'])):
                return False
    return True #return True if no overlaps found

# Function to sum minutes to a time string
def sum_minutes(time_str, minutes):
    time_obj = datetime.strptime(time_str, '%H:%M')
    new_time = time_obj + timedelta(minutes=int(minutes))
    return new_time.strftime('%H:%M')

# Route to modify a draft performance
@app.route('/dashboard/modifica_bozza/<int:id>')
@login_required
def modifica_bozza(id):
    bozza = performance_dao.get_performance_by_id(id)
    if bozza and not bozza['visibile']:
        db_performances = performance_dao.get_performance_list(True)
        stages = palchi_dao.get_stages()
        return render_template('modifica_bozza.html', p_performances=db_performances, p_bozza=bozza, p_stages=stages)
    else:
        flash('Bozza non trovata o già pubblicata', 'danger')
        return redirect(url_for('dashboard'))
    
# Route to delete a performance
@app.route('/dashboard/delete_draft/<int:id>')
@login_required
def delete_draft(id):
    performance = performance_dao.get_performance_by_id(id)
    if performance:
        success = performance_dao.delete_performance(id)
        if success:
            flash('Performance eliminata con successo', 'success')
        else:
            flash('Errore durante l\'eliminazione della performance', 'danger')
    else:
        flash('Performance non trovata', 'danger')
    
    return redirect(url_for('dashboard'))

# Route to publish a draft performance
@app.route('/dashboard/publish_draft/<int:id>')
@login_required
def publish_draft(id):
    performance = dict(performance_dao.get_performance_by_id(id))
    if performance:
        if check_overlaps(performance):
            performance['visibile'] = True
            success = performance_dao.update_performance(performance)
            if success:
                flash('Performance pubblicata con successo', 'success')
            else:
                flash('Errore durante la pubblicazione della performance', 'danger')
        else:
            flash('Impossibile pubblicare la performance a causa di conflitti di orario', 'danger')
    else:
        flash('Bozza non trovata o già pubblicata', 'danger')
    
    return redirect(url_for('dashboard'))

# Route ro view tickets page
@app.route('/biglietti')
def biglietti():
    stats = {}
    stats['Venerdì'] = biglietti_dao.get_stats_per_day('Venerdì')
    stats['Sabato'] = biglietti_dao.get_stats_per_day('Sabato')
    stats['Domenica'] = biglietti_dao.get_stats_per_day('Domenica')

    perc = {}
    perc['Venerdì'] = round((stats['Venerdì'] / 200) * 100)
    perc['Sabato'] = round((stats['Sabato'] / 200) * 100)
    perc['Domenica'] = round((stats['Domenica'] / 200) * 100)

    types = {}
    types['daily'] = biglietti_dao.get_stats_per_type('daily')
    types['2days'] = biglietti_dao.get_stats_per_type('2days')
    types['full'] = biglietti_dao.get_stats_per_type('full')

    if current_user.is_authenticated and current_user.organizzatore:
        return render_template('biglietti.html', p_stats=stats, p_types=types, p_perc=perc)
    elif not current_user.is_authenticated:
        return render_template('biglietti.html', p_can_buy=False)
    else:
        if biglietti_dao.get_biglietti_by_user(current_user.id):
            return render_template('biglietti.html', p_can_buy=False)
        else:
            can_buy = True
            return render_template('biglietti.html', p_can_buy=can_buy, p_stats=stats)
    
# Route to buy tickets
@app.route('/biglietti/acquista', methods=['POST'])
@login_required
def acquista_biglietti():
    if current_user.organizzatore:
        flash('Accesso non autorizzato all\'acquisto di biglietti', 'danger')
        return redirect(url_for('home'))

    ticket = request.form.to_dict()

    if biglietti_dao.get_biglietti_by_user(current_user.id):
        flash('Hai già acquistato un biglietto', 'danger')
        return redirect(url_for('biglietti'))
    
    ticket['utente'] = current_user.id
    ticket['data_acquisto'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if ticket['type'] == '':
        flash('Devi selezionare un tipo di biglietto', 'danger')
        return redirect(url_for('biglietti'))
    elif ticket['type'] == 'daily':
        if ticket['day'] == '':
            flash('Devi selezionare un giorno per il biglietto giornaliero', 'danger')
            return redirect(url_for('biglietti'))
        elif ticket['day'] == 'Venerdì': 
            ticket['Venerdì'] = 1
            ticket['Sabato'] = 0
            ticket['Domenica'] = 0
        elif ticket['day'] == 'Sabato':
            ticket['Venerdì'] = 0
            ticket['Sabato'] = 1
            ticket['Domenica'] = 0
        elif ticket['day'] == 'Domenica':
            ticket['Venerdì'] = 0
            ticket['Sabato'] = 0
            ticket['Domenica'] = 1
    elif ticket['type'] == '2days':
        ticket['Sabato'] = 1
        if ticket['days'] == '':
            flash('Devi selezionare i giorni per il biglietto di 2 giorni', 'danger')
            return redirect(url_for('biglietti'))
        elif ticket['days'] == 'Venerdì-Sabato':
            ticket['Venerdì'] = 1
            ticket['Domenica'] = 0
        elif ticket['days'] == 'Sabato-Domenica':
            ticket['Venerdì'] = 0
            ticket['Domenica'] = 1
    elif ticket['type'] == 'full':
        ticket['Venerdì'] = 1
        ticket['Sabato'] = 1
        ticket['Domenica'] = 1
    else:
        flash('Tipo di biglietto non valido', 'danger')
        return redirect(url_for('biglietti'))  

    success = biglietti_dao.add_ticket(ticket)
    if success:
        flash('Biglietto acquistato con successo!', 'success')
    else:
        flash('Errore durante l\'acquisto del biglietto, riprova', 'danger')

    return redirect(url_for('biglietti'))

# Route to view profile page
@app.route('/profilo')
@login_required
def profile():
    if current_user.organizzatore == 0:
        ticket = biglietti_dao.get_biglietti_by_user(current_user.id)
    else:
        ticket = None
    return render_template('profilo.html', p_ticket=ticket)

# Route for performances page
@app.route('/spettacoli')
def spettacoli():
    db_performances = performance_dao.get_performance_list(True)
    db_stages = palchi_dao.get_stages()
    filtro = {}
    filtro['giorno'] = None
    filtro['palco'] = None
    filtro['artista'] = None
    return render_template('spettacoli.html', p_spettacoli=db_performances, p_palchi=db_stages, p_filtro=filtro)

# Route to filter performances
@app.route('/spettacoli/filtra', methods=['POST'])
def filtro_spettacoli():
    filtro = request.form.to_dict()
    giorno = filtro.get('giorno', '') or None
    palco = filtro.get('palco', '') or None
    genere = filtro.get('genere', '') or None

    performances = performance_dao.filter_performances(giorno, palco, genere)

    db_stages = palchi_dao.get_stages()
    return render_template('spettacoli.html', p_spettacoli=performances, p_palchi=db_stages, p_filtro=filtro)

# Route to stages pages
@app.route('/stages')
def stages():
    db_stages = palchi_dao.get_stages()
    return render_template('stages.html', p_stages=db_stages)

# Routes for add a stage
@app.route('/stages/add_stage', methods=['POST'])
@login_required
def add_stage():
    stage_data = request.form.to_dict()
    if stage_data['nome_palco'] == '':
        flash('Devi inserire un nome per il palco', 'danger')
        return redirect(url_for('stages'))
    if stage_data['descrizione'] == '':
        flash('Devi inserire una descrizione per il palco', 'danger')
        return redirect(url_for('stages'))
    if stage_data['location'] == '':
        flash('Devi inserire una location per il palco', 'danger')
        return redirect(url_for('stages'))
    if stage_data['capienza'] == '':
        flash('Devi inserire una capienza per il palco', 'danger')
        return redirect(url_for('stages'))
    if stage_data['tipologia'] == '':
        flash('devi indicare la tipologia per il palco', 'danger')
    
    # Process images
    image_fields = ['immagine1', 'immagine2', 'immagine3']
    for idx, field in enumerate(image_fields, start=1):
        img_file = request.files.get(field)
        img_save = None
        if img_file and img_file.filename:
            img = Image.open(img_file)

            # Trova il lato minore per ottenere un quadrato
            min_side = min(img.size)

            # Calcola le coordinate per il crop centrale
            left = (img.width - min_side) / 2
            top = (img.height - min_side) / 2
            right = left + min_side
            bottom = top + min_side

            # Ritaglia il quadrato centrale
            img = img.crop((left, top, right, bottom))

            # Utilize the artist's name and index for unique image filenames
            ext = img_file.filename.split('.')[-1]
            img_filename = f"uploads/{stage_data.get('nome_palco').lower()}_{idx}_{str(datetime.now().timestamp())}.{ext}"
            img.save(f"static/{img_filename}")
            img_save = img_filename
        else:
            flash(f'Immagine {idx} non caricata correttamente', 'danger')
            return redirect(url_for('stages'))

        stage_data[field] = img_save if img_file and img_file.filename else None
    
    stage_in_db = palchi_dao.get_stage_by_name(stage_data['nome_palco'])
    if stage_in_db:
        flash('Esiste già un palco con questo nome', 'danger')
        return redirect(url_for('stages'))

    success = palchi_dao.add_stage(stage_data)
    if success:
        flash('Palco aggiunto con successo!', 'success')
    else:
        flash('Errore durante l\'aggiunta del palco, riprova', 'danger')

    return redirect(url_for('stages'))

# Route to modify homepage
@app.route('/modify_home', methods=['POST'])
@login_required
def modify_home():
    # Ottieni la lista degli ID selezionati (può essere None se nessuno selezionato)
    selected_ids = request.form.getlist('performance_ids')
    print(selected_ids)
    # Aggiorna tutte le performance: quelle selezionate is_homepage=True, le altre False
    performance_dao.set_homepage_performances(selected_ids)
    flash('Homepage aggiornata!', 'success')
    return redirect(url_for('dashboard'))

# Route to a single performance
@app.route('/spettacoli/<int:id>')
def single_performance(id):
    performance = performance_dao.get_performance_by_id(id)
    if performance:
        return render_template("spettacolo.html", p_spettacolo=performance)
    else:
        flash("Performance non trovata", "danger")
        return redirect(url_for('spettacoli'))