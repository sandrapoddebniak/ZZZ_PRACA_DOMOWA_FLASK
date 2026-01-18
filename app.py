# -*- coding: utf-8 -*-
# Główny plik aplikacji Book Club - zarządza bazą danych, sesjami i trasami stron.

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

# --- 1. KONFIGURACJA APLIKACJI ---
app = Flask(__name__)
app.secret_key = "sandi_secret_key_2025"  # Klucz do zabezpieczenia sesji (np. logowania)

# Konfiguracja bazy danych SQLite - plik bookclub.db powstanie w folderze projektu
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookclub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. MODELE BAZY DANYCH (Tabele w bazie) ---

class User(db.Model):
    """Tabela przechowująca konta użytkowników."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50))
    password = db.Column(db.String(100), nullable=False)

class Review(db.Model):
    """Tabela przechowująca recenzje książek."""
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    book = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    text = db.Column(db.Text)
    # Domyślna data ustawiona na dzień zaliczenia
    date = db.Column(db.String(20), default="18.01.2026")

class Message(db.Model):
    """Tabela przechowująca wiadomości z formularza kontaktowego."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(100)) # Kolumna na temat wiadomości
    text = db.Column(db.Text)

# --- 3. DANE STATYCZNE (Katalog książek) ---
BOOKS_DISCUSSED = [
    {"title": "Kwiaty dla Algernona", "author": "Daniel Keyes", "img": "https://s.lubimyczytac.pl/upload/books/4875000/4875015/732927-352x500.jpg", "desc": "Trzydziestodwuletni Charlie Gordon..."},
    {"title": "Wiek czerwonych mrówek", "author": "Tania Pijankowa", "img": "https://s.lubimyczytac.pl/upload/books/5048000/5048595/1065896-352x500.jpg", "desc": "Przejmująca powieść o Wielkim Głodzie..."},
    {"title": "Człowiek w poszukiwaniu sensu", "author": "Viktor Frankl", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/czlowiek-w-poszukiwaniu-sensu-b-iext199921942.jpg", "desc": "Wstrząsający esej o pobycie w Auschwitz..."},
    {"title": "Osobiste doświadczenie", "author": "Kenzaburo Oe", "img": "https://s.lubimyczytac.pl/upload/books/5029000/5029192/1011130-352x500.jpg", "desc": "Noblista stawia pytania o odpowiedzialność..."},
    {"title": "Lolita", "author": "Vladimir Nabokov", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/lolita-b-iext202832602.jpg", "desc": "Humbert Humbert – uczony, esteta i romantyk..."},
    {"title": "27 śmierci Toby’ego Obeda", "author": "Joanna Gierak-Onoszko", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/27-smierci-toby-ego-obeda-b-iext199924734.jpg", "desc": "To też jest Kanada..."},
    {"title": "Wyspa", "author": "Aldous Huxley", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/wyspa-b-iext198279066.jpg", "desc": "Idylliczny obraz społeczności..."}
]

BOOKS_UPCOMING = [
    {"title": "Zanim powiesz żegnaj", "author": "Reese Witherspoon, Harlan Coben", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/zanim-powiesz-zegnaj-b-iext202849963.jpg", "desc": "Maggie McCabe..."},
    {"title": "Pomoc domowa", "author": "Freida McFadden", "img": "https://s.lubimyczytac.pl/upload/books/5217000/5217086/1320177-352x500.jpg", "desc": "Millie sprząta luksusową willę..."},
    {"title": "Billy Summers", "author": "Stephen King", "img": "https://s.lubimyczytac.pl/upload/books/5211000/5211561/1310173-352x500.jpg", "desc": "Billy Summers jest snajperem..."},
    {"title": "Poniedziałek z matchą", "author": "Michiko Aoyama", "img": "https://s.lubimyczytac.pl/upload/books/5218000/5218728/1323322-352x500.jpg", "desc": "Ciepła opowieść o nowych początkach..."}
]

# --- 4. FUNKCJE POMOCNICZE ---

def get_clean_reviews():
    """Zamienia obiekty SQLAlchemy na słowniki, aby uniknąć błędów serializacji JSON."""
    raw = Review.query.all()
    return [{"user": r.user, "book": r.book, "text": r.text, "rating": r.rating, "date": r.date} for r in raw]

def init_db():
    """Inicjalizuje bazę danych przy starcie aplikacji."""
    with app.app_context():
        db.create_all()
        # Dodaje domyślne konta, jeśli jeszcze nie istnieją
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", name="Admin", password="admin123"))
            db.session.add(User(username="Anna", name="Anna", password="user123"))
            db.session.commit()

# --- 5. TRASY (Widoki stron) ---

@app.route('/')
def index():
    """Strona główna: przekazuje listy książek i recenzje do szablonu."""
    return render_template(
        'index.html',
        discussed=BOOKS_DISCUSSED,
        upcoming=BOOKS_UPCOMING,
        reviews=get_clean_reviews()
    )

@app.route('/about-me')
def about():
    return render_template('about_me.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Obsługuje formularz kontaktowy. Pobiera pola z request.form."""
    if request.method == 'POST':
        msg = Message(
            name=request.form.get('name'),
            email=request.form.get('email'),
            subject=request.form.get('subject'), # Pobrany temat z pola select
            text=request.form.get('message')
        )
        db.session.add(msg)
        db.session.commit()
        # Przekazujemy success=True, aby wyświetlić komunikat w HTML
        return render_template('contact.html', success=True)
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Prosta rejestracja bez szyfrowania (na potrzeby projektu)
        user = User(
            username=request.form.get('username'),
            name=request.form.get('username').capitalize(),
            password=request.form.get('password')
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username'), 
                                    password=request.form.get('password')).first()
        if user:
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        else:
            # Tu przesyłamy informację o błędzie do HTMLa!
            return render_template('login.html', error="Nieprawidłowy login lub hasło. Spróbuj ponownie.")
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # 1. Python wyciąga dane z formularza (za pomocą 'name')
        new_rev = Review(
            user=session['user'],           # bierze z zalogowanej sesji
            book=request.form.get('book'),   # bierze z <select name="book">
            rating=request.form.get('rating'), # bierze z <input name="rating">
            text=request.form.get('review')   # bierze z <textarea name="review">
        )
        # 2. Dodaje do bazy
        db.session.add(new_rev)
        # 3. Zapisuje na stałe (to jak kliknięcie "Save")
        db.session.commit()
        return redirect(url_for('dashboard'))

    # Przekazujemy wszystkie dane potrzebne do wyświetlenia statystyk i wiadomości
    return render_template(
        'dashboard.html', 
        users=User.query.all(),
        reviews=get_clean_reviews(),
        books=BOOKS_DISCUSSED,
        all_messages=Message.query.all()
    )

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# --- 6. URUCHOMIENIE ---
if __name__ == '__main__':
    init_db() # Upewniamy się, że tabele istnieją
    app.run(debug=True)