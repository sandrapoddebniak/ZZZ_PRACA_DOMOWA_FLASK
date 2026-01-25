# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests

# --- 1. KONFIGURACJA APLIKACJI ---
app = Flask(__name__)
app.secret_key = "sandi_secret_key_2025"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookclub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. MODELE BAZY DANYCH ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50))
    password = db.Column(db.String(100), nullable=False)
    progress = db.relationship('UserProgress', backref='owner', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    book = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    text = db.Column(db.Text)
    date = db.Column(db.String(20), default="18.01.2026")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    text = db.Column(db.Text)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True)
    title = db.Column(db.String(200))
    author = db.Column(db.String(200))
    thumbnail = db.Column(db.String(500))
    page_count = db.Column(db.Integer)
    description = db.Column(db.Text)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    status = db.Column(db.String(30))
    book = db.relationship('Book')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_name = db.Column(db.String(50))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    date = db.Column(db.String(20), default="18.01.2026")

# --- 3. DANE STATYCZNE ---
BOOKS_DISCUSSED = [
    {"title": "Kwiaty dla Algernona", "author": "Daniel Keyes", "img": "https://s.lubimyczytac.pl/upload/books/4875000/4875015/732927-352x500.jpg", "desc": "Trzydziestodwuletni Charlie Gordon..."},
    {"title": "Wiek czerwonych mrówek", "author": "Tania Pijankowa", "img": "https://s.lubimyczytac.pl/upload/books/5048000/5048595/1065896-352x500.jpg", "desc": "Przejmująca powieść o Wielkim Głodzie..."},
    {"title": "Człowiek w poszukiwaniu sensu", "author": "Viktor Frankl", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/czlowiek-w-poszukiwaniu-sensu-b-iext199921942.jpg", "desc": "Wstrząsający esej o pobycie w Auschwitz..."},
    {"title": "Osobiste doświadczenie", "author": "Kenzaburo Oe", "img": "https://s.lubimyczytac.pl/upload/books/5029000/5029192/1011130-352x500.jpg", "desc": "Noblista stawia pytania o odpowiedzialność..."},
    {"title": "Lolita", "author": "Vladimir Nabokov", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/lolita-b-iext202832602.jpg", "desc": "Humbert Humbert..."},
    {"title": "27 śmierci Toby’ego Obeda", "author": "Joanna Gierak-Onoszko", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/27-smierci-toby-ego-obeda-b-iext199924734.jpg", "desc": "To też jest Kanada..."},
    {"title": "Wyspa", "author": "Aldous Huxley", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/wyspa-b-iext198279066.jpg", "desc": "Idylliczny obraz..."}
]

BOOKS_UPCOMING = [
    {"title": "Zanim powiesz żegnaj", "author": "Reese Witherspoon, Harlan Coben", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/zanim-powiesz-zegnaj-b-iext202849963.jpg", "desc": "Maggie McCabe..."},
    {"title": "Pomoc domowa", "author": "Freida McFadden", "img": "https://s.lubimyczytac.pl/upload/books/5217000/5217086/1320177-352x500.jpg", "desc": "Millie sprząta luksusową willę..."},
    {"title": "Billy Summers", "author": "Stephen King", "img": "https://s.lubimyczytac.pl/upload/books/5211000/5211561/1310173-352x500.jpg", "desc": "Billy Summers..."},
    {"title": "Poniedziałek z matchą", "author": "Michiko Aoyama", "img": "https://s.lubimyczytac.pl/upload/books/5218000/5218728/1323322-352x500.jpg", "desc": "Ciepła opowieść..."}
]

# --- 4. FUNKCJE POMOCNICZE ---

def get_clean_reviews():
    try:
        raw = Review.query.all()
        return [{"user": r.user, "book": r.book, "text": r.text, "rating": r.rating, "date": r.date} for r in raw]
    except:
        return []

def init_db():
    with app.app_context():
        db.create_all()

# --- 5. TRASY ---

@app.route('/')
def index():
    #pobieranie recenzji dla sekcji opinii
    all_reviews = Review.query.all()

    #dladej ksiazki z listy BOOKS_DISCUSSED szukamy jej ID w bazie,
    # zeby umozliwosc koemntowanie 
    for book in BOOKS_DISCUSSED:
        db_book = Book.query.filter_by(title=book['title']).first()
        if db_book:
            book['id'] = db_book.id
        else:
            book['id'] = None
            book['comments'] = []
    return render_template('index.html', discussed=BOOKS_DISCUSSED, upcoming=BOOKS_UPCOMING, reviews=get_clean_reviews())

# DODANA TRASA ABOUT - ABY BŁĄD ZNIKNĄŁ
@app.route('/about')
def about():
    return render_template('about_me.html', discussed=BOOKS_DISCUSSED, upcoming=BOOKS_UPCOMING, reviews=get_clean_reviews())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session.clear()
            session['user'] = user.username
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Błędne dane!")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, name=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: 
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')

    # Obsługa dodawania opinii (formularz na Dashboard)
    if request.method == 'POST':
        book_title = request.form.get('book')
        rating = request.form.get('rating')
        review_text = request.form.get('review')
        if book_title and review_text:
            new_rev = Review(user=session['user'], book=book_title, rating=int(rating), text=review_text)
            db.session.add(new_rev)
            db.session.commit()
            return redirect(url_for('dashboard'))

    user_books = UserProgress.query.filter_by(user_id=user_id).all()
    
    # Statystyki
    read_only = [p for p in user_books if p.status == 'Przeczytane']
    stats = {
        "books_read": len(read_only),
        "pages_read": sum([p.book.page_count for p in read_only if p.book and p.book.page_count]) or 0
    }

    # Lista książek do wyboru w formularzu opinii
    user_titles = [p.book.title for p in user_books if p.book]
    manual_titles = [b['title'] for b in BOOKS_DISCUSSED]
    combined_titles = sorted(list(set(user_titles + manual_titles)))

    return render_template('dashboard.html', 
                           reviews=get_clean_reviews(), 
                           stats=stats, 
                           user_books=user_books,
                           available_titles=combined_titles,
                           Comment=Comment)

@app.route('/add-comment/<int:book_id>', methods=['POST'])
def add_comment(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    text = request.form.get('comment_text')
    if text:
        new_comment = Comment(text=text, user_name=session['user'], book_id=book_id)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'user' not in session: return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            resp = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=20").json()
            if "items" in resp:
                for item in resp["items"]:
                    vol = item["volumeInfo"]
                    results.append({
                        'google_id': item['id'],
                        'title': vol.get('title', 'Brak tytułu'),
                        'author': ", ".join(vol.get('authors', ['Nieznany'])),
                        'thumbnail': vol.get('imageLinks', {}).get('thumbnail', ''),
                        'description': vol.get('description', 'Brak opisu.'),
                        'page_count': vol.get('pageCount', 0)
                    })
    return render_template('forum.html', results=results, reviews=get_clean_reviews())

@app.route('/add-to-progress', methods=['POST'])
def add_to_progress():
    if 'user' not in session: return redirect(url_for('login'))
    gid = request.form.get('google_id')
    status = request.form.get('status') 
    user_id = session.get('user_id')
    
    book = Book.query.filter_by(google_id=gid).first()
    if not book:
        book = Book(
            google_id=gid,
            title=request.form.get('title'),
            author=request.form.get('author'),
            thumbnail=request.form.get('thumbnail'),
            page_count=int(request.form.get('page_count', 0)),
            description=request.form.get('description', 'Brak opisu.')
        )
        db.session.add(book)
        db.session.commit()

    exists = UserProgress.query.filter_by(user_id=user_id, book_id=book.id, status=status).first()
    if not exists:
        db.session.add(UserProgress(user_id=user_id, book_id=book.id, status=status))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete-progress/<int:id>', methods=['POST'])
def delete_progress(id):
    if 'user' not in session: return redirect(url_for('login'))
    item = UserProgress.query.get_or_404(id)
    if item.user_id == session.get('user_id'):
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ZAKTUALIZOWANA TRASA KONTAKTU Z OBSŁUGĄ FORMULARZA
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_text = request.form.get('message')
        
        if name and message_text:
            new_msg = Message(name=name, email=email, subject=subject, text=message_text)
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for('index')) # Przekierowanie po sukcesie
            
    return render_template('contact.html', discussed=BOOKS_DISCUSSED, upcoming=BOOKS_UPCOMING)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)