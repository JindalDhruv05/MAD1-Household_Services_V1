from flask_sqlalchemy import SQLAlchemy
from app import app
db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    fullname = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(80), nullable=False)

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    fullname = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=False)
    service_id = db.Column(db.String(80), db.ForeignKey('service.id') ,nullable=False)
    price = db.Column(db.Integer, nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    date_of_request = db.Column(db.Date, nullable=False)
    date_of_service = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(80), nullable=False)
    remarks = db.Column(db.String(80), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(80), nullable=False)

with app.app_context():
    db.create_all()