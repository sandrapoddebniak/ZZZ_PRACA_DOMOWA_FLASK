from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "sandi_secret_key_123"

# DANE UŻYTKOWNIKÓW
users = {
    "alice": {"name": "Alice", "pass": "alice123"},
}

# KSIĄŻKI OMAWIANE
books_discussed = [
    {"title": "Kwiaty dla Algernona", "author": "Daniel Keyes", "img": "https://s.lubimyczytac.pl/upload/books/4875000/4875015/732927-352x500.jpg", "desc": "Trzydziestodwuletni Charlie Gordon bierze udział w eksperymencie zwiększania inteligencji..."},
    {"title": "Wiek czerwonych mrówek", "author": "Tania Pijankowa", "img": "https://s.lubimyczytac.pl/upload/books/5048000/5048595/1065896-352x500.jpg", "desc": "Przejmująca powieść o Wielkim Głodzie w Ukrainie w latach 1932–1933."},
    {"title": "Człowiek w poszukiwaniu sensu", "author": "Viktor Frankl", "img": "https://ecsmedia.pl/cdn-cgi/image/format=webp,width=544,height=544,/c/czlowiek-w-poszukiwaniu-sensu-b-iext199921942.jpg", "desc": "Głęboki esej o przetrwaniu w Auschwitz i poszukiwaniu sensu życia."},
    {"title": "Osobiste doświadczenie", "author": "Kenzaburo Oe", "img": "https://s.lubimyczytac.pl/upload/books/5029000/5029192/1011130-352x500.jpg", "desc": "Noblista stawia pytania o odpowiedzialność za drugiego człowieka."}
]

# KSIĄŻKI NADCHODZĄCE
books_upcoming = [
    {"title": "Pomoc domowa", "author": "Freida McFadden", "img": "https://s.lubimyczytac.pl/upload/books/5217000/5217086/1320177-352x500.jpg", "desc": "Światowy bestseller o sekretach idealnej rodziny Winchesterów."},
    {"title": "Billy Summers", "author": "Stephen King", "img": "https://s.lubimyczytac.pl/upload/books/5211000/5211561/1310173-352x500.jpg", "desc": "Historia snajpera, który przyjmuje ostatnie zlecenie przed emeryturą."},
    {"title": "Poniedziałek z matchą", "author": "Michiko Aoyama", "img": "https://s.lubimyczytac.pl/upload/books/5218000/5218728/1323322-352x500.jpg", "desc": "Ciepła opowieść o nowych początkach przy filiżance herbaty."}
]

reviews = []

@app.route('/')
def index():
    return render_template('index.html', discussed=books_discussed, upcoming=books_upcoming)

@app.route('/about')
def about():
    return render_template('about_me.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('username')
        password = request.form.get('password')
        if login and password:
            users[login] = {"name": login.capitalize(), "pass": password}
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username]['pass'] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        review = {"user": session['user'], "book": request.form.get('book'), "text": request.form.get('review')}
        reviews.append(review)
    return render_template('dashboard.html', users=users, reviews=reviews, books=books_discussed + books_upcoming)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)