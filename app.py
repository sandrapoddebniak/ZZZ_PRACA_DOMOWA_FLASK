from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about-me')
def about_me():
    return render_template('about_me.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message = ""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message_text = request.form.get('message')
        message = f"Dziękujemy za kontakt, {name}! Odpowiemy na {email} wkrótce."
    return render_template('contact.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
