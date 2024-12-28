import datetime
from flask import flash, redirect, render_template, request, url_for, session
from sqlalchemy import null
from app import app
from models import Professional, Review, Service, ServiceRequest, db, Customer
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

@app.route('/')
def index():
    services = Service.query.all()
    param = request.args.get('param')
    query = request.args.get('query')
    if(param=='service'):
        services = Service.query.filter(Service.name.ilike(f'%{query}%')).all()
        return render_template('index.html',services=services)
    elif(param=='pincode'):
        if(len(query)!=6 or not query.isdigit()):
            flash('Invalid pincode')
            return render_template('index.html',services=services)
        return render_template('index.html',services=services,param=param,query=int(query))
    return render_template('index.html',services=services)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register-customer')
def register_customer():
    return render_template('register-customer.html')

@app.route('/register-professional')
def register_professional():
    return render_template('register-professional.html',services=Service.query.all())

def auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

def auth_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login')
            return redirect(url_for('login'))
        if(session['user_id']!='admin'):
            flash('Unauthorized access')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/logout')
def logout():
    session.pop('user_id')
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/register-customer',methods=['POST'])
def register_customer_post():
    username = request.form.get('username')
    password = request.form.get('password')
    fullname = request.form.get('fullname')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    confirm_password = request.form.get('confirm_password')

    if(not username or not password or not confirm_password or not fullname or not address or not pincode):
        flash('Please fill all the fields')
        return redirect(url_for('register_customer'))
    
    if(password != confirm_password):
        flash('Passwords do not match')
        return redirect(url_for('register_customer'))
    
    user = Customer.query.filter_by(username=username).first()
    if(user):
        flash('Username already exists')
        return redirect(url_for('register_customer'))
    
    passhash = generate_password_hash(password)

    new_user = Customer(username=username,passhash=passhash,fullname=fullname,address=address,pincode=pincode)
    db.session.add(new_user)
    db.session.commit()
    flash('Registration successful')
    return redirect(url_for('login'))

@app.route('/register-professional',methods=['POST'])
def register_professional_post():
    username = request.form.get('username')
    password = request.form.get('password')
    fullname = request.form.get('fullname')
    description = request.form.get('description')
    price = request.form.get('price')
    experience = request.form.get('experience')
    service_id = request.form.get('service_id')
    pincode = request.form.get('pincode')
    confirm_password = request.form.get('confirm_password')

    if(not username or not password or not confirm_password or not fullname or not pincode or not description or not price or not experience or not service_id):
        flash('Please fill all the fields')
        return redirect(url_for('register_professional'))
    
    if(password != confirm_password):
        flash('Passwords do not match')
        return redirect(url_for('register_professional'))
    
    if(int(price)<db.session.query(Service.price).filter(Service.id==service_id).first()[0]):
        flash('Price cannot be less than the service price')
        return redirect(url_for('register_professional'))
    
    user = Professional.query.filter_by(username=username).first()
    if(user):
        flash('Username already exists')
        return redirect(url_for('register_professional'))
    
    passhash = generate_password_hash(password)

    new_user = Professional(username=username,passhash=passhash,fullname=fullname,description=description,service_id=service_id,service_pincode=pincode,price=price,experience=experience)
    db.session.add(new_user)
    db.session.commit()
    flash('Registration successful. Wait for approval from admin.')
    return redirect(url_for('login'))

@app.route('/login',methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if(not username or not password or not role):
        flash('Please fill all the fields')
        return redirect(url_for('login'))
    
    if(role=='admin'):
        session['user_id'] = 'admin'
        session['role'] = 'admin'
        flash('Login successful')
        return redirect(url_for('admin'))
    
    elif(role=='customer'):
        user = Customer.query.filter_by(username=username).first()

        if(username=='admin'):
            flash('Unauthorized access')
            return redirect(url_for('login'))

        if(not user):
            flash('Username does not exist')
            return redirect(url_for('login'))
        
        if(not check_password_hash(user.passhash,password)):
            flash('Incorrect password')
            return redirect(url_for('login'))
        
        if(user.flagged=='Flagged'):
            flash('Your account has been flagged. Contact admin for more information')
            return redirect(url_for('login'))
        

        session['user_id'] = user.id
        session['role'] = 'customer'
        flash('Login successful')
        return redirect(url_for('customer_home'))
    else:
        user = Professional.query.filter_by(username=username).first()

        if(not user):
            flash('Username does not exist')
            return redirect(url_for('login'))
        
        if(not check_password_hash(user.passhash,password)):
            flash('Incorrect password')
            return redirect(url_for('login'))
        
        if(user.flagged=='Flagged'):
            flash('Your account has been flagged. Contact admin for more information')
            return redirect(url_for('login'))
        
        if(user.approved==0):
            flash('Your account has not been approved by admin yet. Please wait for approval')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['role'] = 'professional'
        flash('Login successful')
        return redirect(url_for('professional_home'))

#admin routes

@app.route('/admin')
@auth_admin
def admin():
    services = Service.query.all()
    professionals = Professional.query.filter(Professional.approved==True).limit(3).all()

    approved_count = Professional.query.filter_by(approved=True,flagged='Not Flagged').count()
    flagged_count = Professional.query.filter_by(flagged='Flagged').count()
    not_approved_count = Professional.query.filter_by(approved=False).count()
    prof = [flagged_count,approved_count,not_approved_count]

    customers = Customer.query.filter(Customer.username!='admin').limit(3).all()

    cust_flag = Customer.query.filter_by(flagged='Flagged').count()
    cust_not_flag = Customer.query.filter_by(flagged='Not Flagged').filter(Customer.username!='admin').count()
    cust = [cust_flag,cust_not_flag]

    active_request_count = ServiceRequest.query.filter(ServiceRequest.status=='Requested').count() + ServiceRequest.query.filter(ServiceRequest.status=='Assigned').count()
    rejected_request_count = ServiceRequest.query.filter_by(status='Rejected').count()
    completed_request_count = ServiceRequest.query.filter_by(status='Closed').count()
    requests = [rejected_request_count,completed_request_count,active_request_count]

    new_professionals = Professional.query.filter(Professional.approved==False).all()
    customers = Customer.query.filter(Customer.username!='admin').limit(3).all()

    new_professionals = Professional.query.filter(Professional.approved==False).all()
    return render_template('admin.html',services=services,professionals=professionals,customers=customers,new_professionals=new_professionals,prof=prof,cust=cust,requests=requests)

@app.route('/services/add')
@auth_admin
def add_service():
    return render_template('add_service.html')

@app.route('/services/add',methods=['POST'])
@auth_admin
def add_service_post():
    name = request.form.get('name')
    price = request.form.get('price')
    time = request.form.get('time')
    description = request.form.get('description')

    if(not name or not price or not time or not description):
        flash('Please fill all the fields')
        return redirect(url_for('add_service'))
    
    new_service = Service(name=name,price=price,time=time,description=description)
    db.session.add(new_service)
    db.session.commit()
    flash('Service added successfully')
    return redirect(url_for('admin'))

@app.route('/services/<int:id>/edit')
@auth_admin
def edit_service(id):
    service = Service.query.get(id)
    return render_template('edit_service.html',service=service)

@app.route('/services/<int:id>/edit',methods=['POST'])
@auth_admin
def edit_service_post(id):
    name = request.form.get('name')
    price = request.form.get('price')
    time = request.form.get('time')
    description = request.form.get('description')

    if(not name or not price or not time or not description):
        flash('Please fill all the fields')
        return redirect(url_for('edit_service',id=id))
    
    service = Service.query.get(id)
    service.name = name
    service.price = price
    service.time = time
    service.description = description
    for professional in service.professional:
        if professional.price<int(price):
            professional.price = price
    db.session.commit()
    flash('Service updated successfully')
    return redirect(url_for('admin'))

@app.route('/services/<int:id>/delete')
@auth_admin
def delete_service(id):
    service = Service.query.get(id)
    return render_template('delete_service.html',service=service)

@app.route('/services/<int:id>/delete',methods=['POST'])
@auth_admin
def delete_service_post(id):
    service = Service.query.get(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully')
    return redirect(url_for('admin'))

@app.route('/admin/professionals')
@auth_admin
def view_professionals():
    param = request.args.get('param')
    query = request.args.get('query')
    if(param=='username'):
        professionals = Professional.query.filter(Professional.username.ilike(f'%{query}%')).all()
        return render_template('view_professionals.html',professionals=professionals)
    elif(param=='id'):
        if(not query.isdigit()):
            flash('Invalid id')
            return redirect(url_for('view_professionals'))
        professionals = Professional.query.filter(Professional.id==int(query)).all()
        return render_template('view_professionals.html',professionals=professionals)
    
    professionals = Professional.query.filter(Professional.approved==True).all()
    return render_template('view_professionals.html',professionals=professionals)

@app.route('/admin/new_professional/<int:id>/approve')
@auth_admin
def approve_professional(id):
    professional = Professional.query.get(id)
    return render_template('approve_professional.html',professional=professional)

@app.route('/admin/new_professional/<int:id>/approve',methods=['POST'])
@auth_admin
def approve_professional_post(id):
    professional = Professional.query.get(id)
    professional.approved = True
    db.session.commit()
    flash('Professional approved successfully')
    return redirect(url_for('admin'))

@app.route('/flag/professional/<int:id>')
@auth_admin
def flag_professional(id):
    professional = Professional.query.get(id)
    if(professional.flagged=='Flagged'):
        professional.flagged = 'Not Flagged'
    else:
        professional.flagged = 'Flagged'
    db.session.commit()
    flash('Professional status updated')
    return redirect(url_for('admin'))

@app.route('/professionals/<int:id>/delete')
@auth_admin
def delete_professional(id):
    professional = Professional.query.get(id)
    return render_template('delete_professional.html',professional=professional)

@app.route('/professionals/<int:id>/delete',methods=['POST'])
@auth_admin
def delete_professional_post(id):
    professional = Professional.query.get(id)
    db.session.delete(professional)
    db.session.commit()
    flash('Professional deleted successfully')
    return redirect(url_for('admin'))

@app.route('/admin/customers')
@auth_admin
def view_customers():
    customers = Customer.query.filter(Customer.username!='admin').all()
    return render_template('view_customers.html',customers=customers)

@app.route('/flag/customer/<int:id>')
@auth_admin
def flag_customer(id):
    customer = Customer.query.get(id)
    if(customer.flagged=='Flagged'):
        customer.flagged = 'Not Flagged'
    else:
        customer.flagged = 'Flagged'
    db.session.commit()
    flash('Customer status updated')
    return redirect(url_for('admin'))

@app.route('/customers/<int:id>/delete')
@auth_admin
def delete_customer(id):
    customer = Customer.query.get(id)
    return render_template('delete_customer.html',customer=customer)

@app.route('/customers/<int:id>/delete',methods=['POST'])
@auth_admin
def delete_customer_post(id):
    customer = Customer.query.get(id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully')
    return redirect(url_for('admin'))

@app.route('/admin/profile')
@auth_admin
def admin_profile():
    user = Customer.query.filter_by(username='admin').first()
    return render_template('admin_profile.html',user=user)

@app.route('/admin/profile', methods=['POST'])
@auth_admin
def admin_profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    npassword = request.form.get('npassword')

    if(not username or not cpassword or not npassword):
        flash('Please fill all the fields')
        return redirect(url_for('admin_profile'))
    
    user = Customer.query.filter_by(username='admin').first()
    if(not check_password_hash(user.passhash,cpassword)):
        flash('Incorrect password')
        return redirect(url_for('admin_profile'))

    user.passhash = generate_password_hash(npassword)
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('admin'))

#customer routes

@app.route('/customer_home')
@auth
def customer_home():
    user=Customer.query.get(session['user_id'])
    bookings = ServiceRequest.query.filter(ServiceRequest.customer_id==session['user_id']).all()
    #add approved condition and not flagged condition
    professionals = Professional.query.all()
    services = Service.query.all()
    return render_template('customer_home.html',user=user,bookings=bookings,professionals=professionals,services=services)    

@app.route('/customer_home/profile')
@auth
def customer_profile():
    user=Customer.query.get(session['user_id'])
    return render_template('customer_profile.html',user=user)

@app.route('/customer_home/profile', methods=['POST'])
def customer_profile_post():
    username = request.form.get('username')
    fullname = request.form.get('fullname')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    cpassword = request.form.get('cpassword')
    npassword = request.form.get('npassword')

    if(not username or not cpassword or not npassword):
        flash('Please fill all the fields')
        return redirect(url_for('customer_profile'))
    
    user = Customer.query.get(session['user_id'])
    if(not check_password_hash(user.passhash,cpassword)):
        flash('Incorrect password')
        return redirect(url_for('customer_profile'))

    if username!=user.username:
        new_username = Customer.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('customer_profile'))

    user.username = username
    user.fullname = fullname
    user.address = address
    user.pincode = pincode
    user.passhash = generate_password_hash(npassword)
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('customer_home'))

@app.route('/customer_home/book_service/<int:id>')
@auth
def book_service(id):
    service = Service.query.get(Professional.query.get(id).service_id)
    return render_template('book_service.html')

@app.route('/customer_home/book_service/<int:id>',methods=['POST'])
@auth
def book_service_post(id):
    date_of_service = request.form.get('date')
    date_of_service = datetime.datetime.strptime(date_of_service, '%Y-%m-%d').date()
    remarks = request.form.get('remarks')

    if(not date_of_service or not remarks):
        flash('Please fill all the fields')
        return redirect(url_for('book_service',id=id))
    
    new_request = ServiceRequest(
        customer_id=session['user_id'],
        service_id=Professional.query.get(id).service_id,
        professional_id=id,
        date_of_request=datetime.datetime.now().date(),
        date_of_service=date_of_service,
        remarks=remarks
        )
    db.session.add(new_request)
    db.session.commit()
    flash('Service booked successfully')
    return redirect(url_for('customer_home'))

#edit booking
@app.route('/customer_home/edit_booking/<int:id>')
@auth
def edit_booking(id):
    booking = ServiceRequest.query.get(id)
    return render_template('edit_booking.html',booking=booking)

@app.route('/customer_home/edit_booking/<int:id>',methods=['POST'])
@auth
def edit_booking_post(id):
    date_of_service = request.form.get('date')
    date_of_service = datetime.datetime.strptime(date_of_service, '%Y-%m-%d').date()
    remarks = request.form.get('remarks')

    if(not date_of_service or not remarks):
        flash('Please fill all the fields')
        return redirect(url_for('edit_booking',id=id))
    
    booking = ServiceRequest.query.get(id)
    booking.date_of_service = date_of_service
    booking.remarks = remarks
    db.session.commit()
    flash('Booking updated successfully')
    return redirect(url_for('customer_home'))

#complete booking
@app.route('/customer_home/complete_booking/<int:id>')
@auth
def complete_booking(id):
    booking = ServiceRequest.query.get(id)
    if(booking.status=='Requested'):
        flash('Booking not yet accepted by professional.')
        return redirect(url_for('customer_home'))
    return render_template('complete_booking.html',booking=booking)

@app.route('/customer_home/complete_booking/<int:id>',methods=['POST'])
@auth
def complete_booking_post(id):
    booking = ServiceRequest.query.get(id)
    rating = request.form.get('rating')
    remarks = request.form.get('remarks')
    professional = Professional.query.get(booking.professional_id)
    professional.rating = (professional.rating+int(rating))//2
    review = Review(
        service_request_id=id,
        professional_rating=rating,
        remarks=remarks)
    booking.status = 'Closed'
    db.session.add(review)
    db.session.commit()
    flash('Booking completed successfully')
    return redirect(url_for('customer_home'))

@app.route('/customer_home/view_review/<int:id>')
@auth
def view_review(id):
    request = ServiceRequest.query.get(id)
    review = Review.query.filter(Review.service_request_id==id).first()
    return render_template('view_review.html',review=review,request=request)

#professional routes
@app.route('/professional_home')
@auth
def professional_home():
    user=Professional.query.get(session['user_id'])
    bookings = ServiceRequest.query.filter(ServiceRequest.professional_id==session['user_id']).all()
    customers = Customer.query.all()
    return render_template('professional_home.html',user=user,bookings=bookings,customers=customers)

@app.route('/accept_booking/<int:id>')
@auth
def accept_request(id):
    booking = ServiceRequest.query.get(id)
    if(booking.status=='Assigned'):
        flash('Booking already accepted')
        return redirect(url_for('professional_home'))
    booking.status = 'Assigned'
    db.session.commit()
    flash('Booking accepted successfully')
    return redirect(url_for('professional_home'))

@app.route('/reject_booking/<int:id>')
@auth
def reject_request(id):
    booking = ServiceRequest.query.get(id)
    if(booking.status=='Rejected'):
        flash('Booking already rejected')
        return redirect(url_for('professional_home'))
    booking.status = 'Rejected'
    db.session.commit()
    flash('Booking rejected successfully')
    return redirect(url_for('professional_home'))

@app.route('/professional_home/add_review/<int:id>')
@auth
def add_review(id):
    booking = ServiceRequest.query.get(id)
    review = Review.query.filter(Review.service_request_id==id).first()
    if(review.customer_rating==None):
        return render_template('add_review.html',booking=booking)
    else:
        return render_template('view_review_professional.html',review=review)   

@app.route('/professional_home/add_review/<int:id>',methods=['POST'])
@auth
def add_review_post(id):
    rating = request.form.get('rating')
    review = Review.query.filter(Review.service_request_id==id).first()
    customer = Customer.query.get(ServiceRequest.query.get(id).customer_id)
    customer.rating = (customer.rating+int(rating))//2
    review.customer_rating = rating
    db.session.commit()
    flash('Review added successfully')
    return redirect(url_for('professional_home'))

@app.route('/professional_home/profile')
@auth
def professional_profile():
    user=Professional.query.get(session['user_id'])
    service = Service.query.get(user.service_id)
    return render_template('professional_profile.html',user=user,service=service)

@app.route('/professional_home/profile', methods=['POST'])
def professional_profile_post():
    username = request.form.get('username')
    fullname = request.form.get('fullname')
    description = request.form.get('description')
    price = request.form.get('price')
    experience = request.form.get('experience')
    pincode = request.form.get('pincode')
    cpassword = request.form.get('cpassword')
    npassword = request.form.get('npassword')

    if(not username or not cpassword or not npassword or not fullname or not description or not price or not experience or not pincode):
        flash('Please fill all the fields')
        return redirect(url_for('professional_profile'))
    
    user = Professional.query.get(session['user_id'])
    if(not check_password_hash(user.passhash,cpassword)):
        flash('Incorrect password')
        return redirect(url_for('professional_profile'))

    if username!=user.username:
        new_username = Professional.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('professional_profile'))

    user.username = username
    user.fullname = fullname
    user.description = description
    user.price = price
    user.experience = experience
    user.service_pincode = pincode
    user.passhash = generate_password_hash(npassword)
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('professional_home'))