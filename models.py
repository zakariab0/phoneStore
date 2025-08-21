from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime, date

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('owner', 'worker'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class CashRegister(db.Model):
    __tablename__ = 'cash_register'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    opening_cash = db.Column(db.Numeric(10,2), nullable=False)
    closing_cash = db.Column(db.Numeric(10,2))
    total_sales = db.Column(db.Numeric(10,2), default=0)
    declared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_open = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # Relationship
    worker = db.relationship('User', backref='cash_declarations')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    cost_price = db.Column(db.Numeric(10,2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProductLog(db.Model):
    __tablename__ = 'product_logs'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    worker_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.Enum('added', 'removed', 'sold'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))
    log_date = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.Enum('product', 'phone'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    worker_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    selling_price = db.Column(db.Numeric(10,2), nullable=False)
    sale_date = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    sale_type = db.Column(db.String(20), default='product')

class Phone(db.Model):
    __tablename__ = 'phone'  # Note: your table is named 'phone' not 'phones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    storage = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    condition = db.Column(db.String(10), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    cost_price = db.Column(db.Float, nullable=False)

