import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI = "sqlite:///"+os.path.join(app.instance_path, "meoknow.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS = False 
    )
    db.init_app(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
        os.makedirs(os.path.join(app.instance_path, 'images'))
    except OSError:
        pass
    
    from . import cat

    cat.add_functions(app)
    
    with app.app_context():
        db.create_all()

    # a simple page that says hello
    @app.route('/hello/')
    def hello():
        return 'Hello, World!'

    return app