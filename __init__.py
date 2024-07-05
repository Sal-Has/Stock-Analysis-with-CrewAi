# __init__.py
from flask import Flask
from config import Config
from models import db, bcrypt
from flask_mail import Mail
from flask_caching import Cache
from flask_migrate import Migrate
from flask_uploads import UploadSet, configure_uploads, IMAGES

photos = UploadSet('photos', IMAGES)

mail = Mail()
cache = Cache()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.secret_key ="owfhg937219hwefobduodedcbudi";

    app.config.from_object(Config)
    app.config['CACHE_TYPE'] = 'simple'  # Simple in-memory cache for demonstration
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Default timeout for cached responses
    app.config['UPLOAD_FOLDER'] = 'static/uploads'

    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    migrate.init_app(app)
    configure_uploads(app, photos)

    with app.app_context():
        db.create_all()

    from views import main_bp
    app.register_blueprint(main_bp)

    return app
