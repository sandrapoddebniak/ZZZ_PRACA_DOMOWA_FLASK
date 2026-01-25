# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
import requests
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

# --- 1. KONFIGURACJA APLIKACJI ---
app = Flask(__name__)
app.secret_key = "sandi_secret_key_2026" 

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bookclub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. DEKORATOR DOSTEPU ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Musisz się zalogować, aby zobaczyć tę stronę.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 3. MODELE BAZY DANYCH ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50))
    # Zwiększono długość, aby pomieścić nowoczesne hashe (np. scrypt)
    password = db.Column(db.String(512), nullable=False) 
    progress = db.relationship('UserProgress', backref='owner', lazy=True, cascade="all, delete-orphan")
    reviews_rel = db.relationship('Review', backref='author', lazy=True)
    comments_rel = db.relationship('Comment', backref='author', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # user_name_display zostaje u Ciebie, ale docelowo lepiej brać z relacji 'author'
    user_name_display = db.Column(db.String(50)) 
    book_title = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    thumbnail = db.Column(db.String(500))
    page_count = db.Column(db.Integer, default=0)
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Pole user_name zachowane, ale w dashboardzie lepiej użyć c.author.username
    user_name = db.Column(db.String(50)) 
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# --- 4. DANE STATYCZNE ---
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

# --- 5. FUNKCJE POMOCNICZE ---

def get_clean_reviews():
    # Usunięto pusty except dla lepszego debugowania
    return Review.query.order_by(Review.date.desc()).all()

# --- 6. TRASY ---

@app.route('/', methods=['GET', 'POST']) # Dodaliśmy metody
def index():
    if request.method == 'POST':
        # Jeśli jakimś cudem formularz trafi tutaj, po prostu odświeżamy stronę
        return redirect(url_for('index'))
        
    return render_template('index.html', 
                           discussed=BOOKS_DISCUSSED, 
                           upcoming=BOOKS_UPCOMING, 
                           reviews=get_clean_reviews())

@app.route('/get-book-details/<title>')
def get_book_details(title):
    book = Book.query.filter_by(title=title).first()
    if not book: return jsonify({"error": "Błąd"}), 404
    comments = Comment.query.filter_by(book_id=book.id).order_by(Comment.date.desc()).all()
    return jsonify({
        "id": book.id,
        "comments": [{"user": c.user_name, "text": c.text, "date": c.date.strftime('%d.%m.%Y %H:%M')} for c in comments]
    })

@app.route('/about')
def about():
    return render_template('about_me.html', discussed=BOOKS_DISCUSSED, upcoming=BOOKS_UPCOMING, reviews=get_clean_reviews())

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject')
        message_text = request.form.get('message', '').strip()
        if name and message_text:
            new_msg = Message(name=name, email=email, subject=subject, text=message_text)
            db.session.add(new_msg)
            db.session.commit()
            flash('Wiadomość została wysłana! Dziękujemy.', 'success')
            return redirect(url_for('contact'))
    return render_template('contact.html', reviews=get_clean_reviews())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if not u or not p:
            flash('Wpisz nazwę użytkownika i hasło.', 'error')
            return render_template('login.html')
            
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session.clear()
            session['user_id'] = user.id
            session['user'] = user.username
            session['is_admin'] = (user.username == 'admin')
            return redirect(url_for('dashboard'))
        flash('Błędne dane logowania!', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username and password:
            if not User.query.filter_by(username=username).first():
                hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
                new_user = User(username=username, name=username, password=hashed_pw)
                db.session.add(new_user)
                db.session.commit()
                flash('Konto stworzone! Możesz się zalogować.', 'success')
                return redirect(url_for('login'))
            flash('Taki użytkownik już istnieje.', 'error')
        else:
            flash('Uzupełnij wszystkie pola.', 'error')
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if request.method == 'POST' and 'review' in request.form:
        book_title = request.form.get('book')
        rating = request.form.get('rating')
        review_text = request.form.get('review', '').strip()
        if book_title and review_text:
            new_rev = Review(user_id=user_id, user_name_display=session['user'], 
                             book_title=book_title, rating=int(rating), text=review_text)
            db.session.add(new_rev)
            db.session.commit()
            flash('Twoja opinia została dodana!', 'success')
            return redirect(url_for('dashboard'))

    # Optymalizacja N+1: pobieramy UserProgress razem z danymi książek (joinedload)
    user_books = UserProgress.query.filter_by(user_id=user_id).options(joinedload(UserProgress.book)).all()
    all_users = User.query.all()
    all_messages = Message.query.order_by(Message.date.desc()).all() if session.get('is_admin') else []
    
    read_only = [p for p in user_books if p.status == 'Przeczytane']
    stats = {
        "books_read": len(read_only),
        "pages_read": sum([p.book.page_count for p in read_only if p.book and p.book.page_count])
    }

    user_titles = [p.book.title for p in user_books if p.book]
    manual_titles = [b['title'] for b in BOOKS_DISCUSSED]
    combined_titles = sorted(list(set(user_titles + manual_titles)))

    all_reviews = Review.query.order_by(Review.date.desc()).all()

    return render_template('dashboard.html', 
                           user=user,
                           users=all_users,
                           reviews=all_reviews, 
                           stats=stats, 
                           user_books=user_books,
                           books=Book.query.all(),
                           available_titles=combined_titles,
                           all_messages=all_messages)

@app.route('/add-comment/<int:book_id>', methods=['POST'])
@login_required
def add_comment(book_id):
    text = request.form.get('comment_text', '').strip()
    if text:
        new_comment = Comment(text=text, user_id=session['user_id'], 
                              user_name=session['user'], book_id=book_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Komentarz został dodany!', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    results = []
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            try:
                # Dodano timeout, aby aplikacja nie wisiała w nieskończoność
                resp = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=20", timeout=10).json()
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
            except Exception as e:
                flash('Błąd podczas łączenia z Google Books API.', 'error')
                print(f"Błąd API: {e}")
    return render_template('forum.html', results=results, reviews=get_clean_reviews())

@app.route('/add-to-progress', methods=['POST'])
@login_required
def add_to_progress():
    gid = request.form.get('google_id')
    status = request.form.get('status') 
    user_id = session.get('user_id')
    
    # Bezpieczna obsługa page_count
    try:
        p_count = int(request.form.get('page_count', 0))
    except (ValueError, TypeError):
        p_count = 0

    book = Book.query.filter_by(google_id=gid).first()
    if not book:
        book = Book(
            google_id=gid, 
            title=request.form.get('title'), 
            author=request.form.get('author'), 
            thumbnail=request.form.get('thumbnail'), 
            page_count=p_count, 
            description=request.form.get('description', 'Brak opisu.')
        )
        db.session.add(book)
        db.session.commit()
    
    if not UserProgress.query.filter_by(user_id=user_id, book_id=book.id, status=status).first():
        db.session.add(UserProgress(user_id=user_id, book_id=book.id, status=status))
        db.session.commit()
        flash(f'Dodano do listy!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete-review-action/<int:review_id>', methods=['POST'])
@login_required
def delete_review_action(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id == session.get('user_id') or session.get('is_admin'):
        db.session.delete(review)
        db.session.commit()
        flash('Recenzja została usunięta.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/delete-progress/<int:progress_id>', methods=['POST'])
@login_required
def delete_progress(progress_id):
    progress = UserProgress.query.get_or_404(progress_id)
    if progress.user_id == session.get('user_id'):
        db.session.delete(progress)
        db.session.commit()
        flash('Książka usunięta z listy.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(
                username='admin', 
                name='Admin', 
                password=generate_password_hash('admin123', method='pbkdf2:sha256')
            ))
            
        for b in BOOKS_DISCUSSED + BOOKS_UPCOMING:
            if not Book.query.filter_by(title=b['title']).first():
                db.session.add(Book(
                    title=b['title'], 
                    author=b['author'], 
                    thumbnail=b['img'], 
                    description=b['desc'], 
                    page_count=300
                ))
        db.session.commit()
    app.run(debug=True, port=5001)