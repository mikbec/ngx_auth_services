import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
from flask_babel import Babel
#from flask_babel import lazy_gettext as _l
from app import config


#db = SQLAlchemy()
#migrate = Migrate()
babel = Babel()

def create_app(config_name):
    # get application config
    config_obj = config.get_config(config_name)

    # now create our app object
    static_url_path = config_obj.URL_MASTER_CONTEXT + 'static'
    app = Flask(__name__,
                instance_relative_config = True,
                static_url_path = static_url_path
               )
    app.config.from_object(config_obj)
    config_obj.init_app(app)

    #db.init_app(app)
    #migrate.init_app(app, db)
    babel.init_app(app)

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
        app.logger.info('Application startup')

    return app

