from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate


db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    from .routes import admin, professional, customer, auth
    app.register_blueprint(admin.bp)
    app.register_blueprint(professional.bp)
    app.register_blueprint(customer.bp)
    app.register_blueprint(auth.auth)

    return app
