import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from flask_bootstrap import Bootstrap
from app import config


#db = SQLAlchemy()
#migrate = Migrate()
babel = Babel()
bootstrap = Bootstrap()

def create_app(config_name, app_main_file=None):
    # get application config
    if app_main_file == None:
        app_main_path = os.path.dirname(os.path.abspath(__file__))
    else:
        app_main_path = os.path.dirname(os.path.abspath(app_main_file))
    print("app_main_path is: " + app_main_path)
    config_obj = config.create_config_obj(config_name)
    config_obj.update_config_obj(app_main_path)

    # now create our app object
    static_url_path = config_obj.URL_MASTER_CONTEXT + 'static'
    app = Flask(__name__,
                instance_relative_config = True,
                static_url_path = static_url_path
               )
    app.config.from_object(config_obj)

    #db.init_app(app)
    #migrate.init_app(app, db)
    babel.init_app(app)
    bootstrap.init_app(app)

    from app.auth_saml import bp as auth_saml_bp
    url_prefix = app.config['URL_MASTER_CONTEXT'] + 'auth_saml'
    app.register_blueprint(auth_saml_bp, url_prefix=url_prefix)

    #if not app.config['TESTING'] and not app.config['DEBUG']:
    if not app.config['TESTING']:
        if not os.path.exists('logs'):
           os.mkdir('logs')
        file_handler = RotatingFileHandler(
                           'logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(
                         logging.Formatter(
                             '%(asctime)s %(levelname)s: %(message)s '
                             '[in %(pathname)s:%(lineno)d]'
                         )
                     )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info(_l('Application startup'))

    return app

