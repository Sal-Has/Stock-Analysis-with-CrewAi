# config.py
import os
class Config:
    SECRET_KEY = '1353632rvdshgvccs'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:208hr882@localhost/user_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'salimiddi64@gmail.com'
    MAIL_PASSWORD = 'aaep lfig buei qkjv'
    UPLOADED_PHOTOS_DEST = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
