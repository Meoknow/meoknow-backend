import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def create_app(test_config=None):
    # create and configure the app
    if test_config is None or "instance_path" not in test_config:
        app = Flask(__name__, instance_relative_config=True)
    else:
        app = Flask(__name__, instance_path=test_config["instance_path"], instance_relative_config=True)
        
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
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(app.instance_path, 'images'))
    except OSError:
        pass
    
    
    with app.app_context():
        from . import cat
        from . import auth
        from . import comment
        from . import admin
        from . import map

        cat.add_functions(app)
        auth.add_functions(app)
        comment.add_functions(app)
        admin.add_functions(app)
        map.add_functions(app)
        db.create_all()

    # a simple page that says hello
    @app.route('/hello/')
    def hello():
        return 'Hello, World!'

    return app