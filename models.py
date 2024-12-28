from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from app import app
from werkzeug.security import generate_password_hash

db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    fullname = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=3)
    flagged = db.Column(db.Enum('Flagged','Not Flagged'), nullable=False, default='Not Flagged')
    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(80), nullable=False)
    professional = db.relationship('Professional', backref='service', lazy=True, cascade='all, delete')

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    fullname = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=False)
    service_id = db.Column(db.String(80), db.ForeignKey('service.id') ,nullable=False)
    service_pincode = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=3)
    flagged = db.Column(db.Enum('Flagged','Not Flagged'), nullable=False, default='Not Flagged')
    approved = db.Column(db.Boolean, nullable=False, default=False)
    service_requests = db.relationship('ServiceRequest', backref='professional', lazy=True)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    date_of_request = db.Column(db.Date, nullable=False)
    date_of_service = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Requested','Assigned','Closed','Rejected'), nullable=False, default='Requested')
    remarks = db.Column(db.String(80),)
    review = db.relationship('Review', backref='service_request', lazy=True, uselist=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    customer_rating = db.Column(db.Integer, nullable=True)
    professional_rating = db.Column(db.Integer, nullable=True)
    remarks = db.Column(db.String(80), nullable=True)

with app.app_context():
    
    # db.session.execute(text('DROP TABLE review'))
    db.create_all()
    if(not Customer.query.filter_by(username='admin').first()):
        admin = Customer(username='admin', passhash=generate_password_hash('admin'), fullname='admin', address='admin', pincode=000000)
        db.session.add(admin)
        db.session.commit()