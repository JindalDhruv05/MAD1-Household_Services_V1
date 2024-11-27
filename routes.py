from flask import render_template
from app import app

@app.route('/')
def index():
    return render_template('index.html',name='Dhruv')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')