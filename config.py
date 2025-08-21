import os

class Config:
    SECRET_KEY = os.urandom(24)
    # Local MySQL database configuration
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/med?charset=utf8mb4'
    # Remote MySQL database configuration (example for PythonAnywhere)
    # Replace <username>, <password>, <host>, <dbname> with your actual credentials
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/med?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
