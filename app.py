# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "sandi_secret_key_2025"

# --- KONFIGURACJA SQL ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookclub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELE BAZY DANYCH ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(100))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    book = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    text = db.Column(db.Text)
    date = db.Column(db.String(20), default="10.01.2026")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    text = db.Column(db.Text)

# TWORZENIE BAZY
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", name="admin", password="admin123"))
        db.session.add(User(username="Anna", name="Anna", password="user123"))
        db.session.add(User(username="Maria", name="Maria", password="user123"))
        db.session.commit()

# --- DANE KSIĄŻEK ---
books_discussed = [
    {"title": "Kwiaty dla Algernona", "author": "Daniel Keyes", "img": "https://s.lubimyczytac.pl/upload/books/4875000/4875015/732927-352x500.jpg", "desc": "Trzydziestodwuletni Charlie Gordon jest niepełnosprawny intelektualnie..."},
    {"title": "Wiek czerwonych mrówek", "author": "Tania Pijankowa", "img": "https://s.lubimyczytac.pl/upload/books/5048000/5048595/1065896-352x500.jpg", "desc": "Przejmująca powieść o Wielkim Głodzie w Ukrainie..."},
    {"title": "Człowiek w poszukiwaniu sensu", "author": "Viktor Frankl", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/czlowiek-w-poszukiwaniu-sensu-b-iext199921942.jpg", "desc": "Wstrząsający esej o pobycie w Auschwitz..."},
    {"title": "Osobiste doświadczenie", "author": "Kenzaburo Oe", "img": "https://s.lubimyczytac.pl/upload/books/5029000/5029192/1011130-352x500.jpg", "desc": "Noblista stawia pytania o odpowiedzialność za drugiego człowieka..."}
]

books_upcoming = [
    {"title": "Zanim powiesz żegnaj", "author": "Reese Witherspoon, Harlan Coben", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/zanim-powiesz-zegnaj-b-iext202849963.jpg", "desc": "Maggie McCabe, elitarny chirurg..."},
    {"title": "Pomoc domowa", "author": "Freida McFadden", "img": "https://s.lubimyczytac.pl/upload/books/5217000/5217086/1320177-352x500.jpg", "desc": "Millie sprząta luksusową willę Winchesterów..."},
    {"title": "Billy Summers", "author": "Stephen King", "img": "https://s.lubimyczytac.pl/upload/books/5211000/5211561/1310173-352x500.jpg", "desc": "Billy Summers jest snajperem, który eliminuje tylko złych ludzi..."},
    {"title": "Poniedziałek z matchą", "author": "Michiko Aoyama", "img": "https://s.lubimyczytac.pl/upload/books/5218000/5218728/1323322-352x500.jpg", "desc": "Ciepła opowieść o nowych początkach przy filiżance matchy..."}
]

# --- POMOCNICZA FUNKCJA DO JSON ---
def get_clean_reviews():
    raw = Review.query.all()
    return [{"user": r.user, "book": r.book, "text": r.text, "rating": r.rating} for r in raw]

# --- TRASY ---

@app.route('/')
def index():
    return render_template(
        'index.html',
        discussed=books_discussed,
        upcoming=books_upcoming,
        reviews=get_clean_reviews(),
        users=User.query.all()
    )

@app.route('/about-me')
def about():
    return render_template('about_me.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        new_msg = Message(
            name=request.form.get('name'),
            email=request.form.get('email'),
            text=request.form.get('message')
        )
        db.session.add(new_msg)
        db.session.commit()
        return render_template('contact.html', success="Wiadomość została wysłana!")
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('username')
        password = request.form.get('password')
        if login and password:
            new_user = User(username=login, name=login.capitalize(), password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Błędny login lub hasło")
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_rev = Review(
            user=session['user'],
            book=request.form.get('book'),
            rating=request.form.get('rating'),
            text=request.form.get('review')
        )
        db.session.add(new_rev)
        db.session.commit()
        
    return render_template(
        'dashboard.html', 
        users=User.query.all(), 
        reviews=get_clean_reviews(), 
        books=books_discussed, 
        all_messages=Message.query.all()
    )

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)