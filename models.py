from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, password, nome, cognome, organizzatore, data_registrazione, sesso):
        self.id = id
        self.email = email
        self.password = password
        self.nome = nome
        self.cognome = cognome
        self.organizzatore = organizzatore
        self.data_registrazione = data_registrazione
        self.sesso = sesso