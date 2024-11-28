from flask import flash, redirect, render_template, request, url_for, session
from app import app
from models import db, Customer
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

def auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/logout')
def logout():
    session.pop('user_id')
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/register',methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    fullname = request.form.get('fullname')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    confirm_password = request.form.get('confirm_password')

    if(not username or not password or not confirm_password or not fullname or not address or not pincode):
        flash('Please fill all the fields')
        return redirect(url_for('register'))
    
    if(password != confirm_password):
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    user = Customer.query.filter_by(username=username).first()
    if(user):
        flash('Username already exists')
        return redirect(url_for('register'))
    
    passhash = generate_password_hash(password)

    new_user = Customer(username=username,passhash=passhash,fullname=fullname,address=address,pincode=pincode)
    db.session.add(new_user)
    db.session.commit()
    flash('Registration successful')
    return redirect(url_for('login'))

@app.route('/login',methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if(not username or not password):
        flash('Please fill all the fields')
        return redirect(url_for('login'))
    
    user = Customer.query.filter_by(username=username).first()
    if(not user):
        flash('Username does not exist')
        return redirect(url_for('login'))
    
    if(not check_password_hash(user.passhash,password)):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    flash('Login successful')
    return redirect(url_for('customer_home'))

@app.route('/customer_home')
@auth
def customer_home():
    user=Customer.query.get(session['user_id'])
    return render_template('customer_home.html',user=user)    

@app.route('/customer_home', methods=['POST'])
def customer_update():
    username = request.form.get('username')
    fullname = request.form.get('fullname')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    cpassword = request.form.get('cpassword')
    npassword = request.form.get('npassword')

    if(not username or not cpassword or not npassword):
        flash('Please fill all the fields')
        return redirect(url_for('customer_home'))
    
    user = Customer.query.get(session['user_id'])
    if(not check_password_hash(user.passhash,cpassword)):
        flash('Incorrect password')
        return redirect(url_for('customer_home'))

    if username!=user.username:
        new_username = Customer.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('customer_home'))

    user.username = username
    user.fullname = fullname
    user.address = address
    user.pincode = pincode
    user.passhash = generate_password_hash(npassword)
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('customer_home'))