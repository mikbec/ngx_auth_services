import os
#_saml_base_cfg_dir = os.path.abspath(os.path.dirname(__file__))
_saml_base_cfg_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')

class BaseConfig(object):
    '''
    The base class for configuration

    You should overwrite settings in sub classes.
    '''
    CONFIG_NAME = 'BaseConfig'

    SECRET_KEY = '!!! The python3-saml toolkit secret key you have to change! !!!'
    SAML_PATH  = \
            os.environ.get('NGX_SAML_AUTH_SAML_PATH') or \
            _saml_base_cfg_dir

    # URL_MASTER_CONTEXT must be empty or must begin and end with "/".
    URL_MASTER_CONTEXT = \
            os.environ.get('NGX_SAML_AUTH_URL_MASTER_CONTEXT') or \
            '/auth_services/'

    def update_config_obj(self, app_main_path):
        # set SECRET_KEY
        if 'NGX_SAML_AUTH_SECRET_KEY' in os.environ:
            self.SECRET_KEY = os.environ.get('NGX_SAML_AUTH_SECRET_KEY')
        elif app_main_path and os.path.isfile(os.path.join(app_main_path, 'secret-key.txt')):
            self.SECRET_KEY = open(os.path.join(app_main_path, 'secret-key.txt')).read()
        elif os.path.isfile(os.path.join(_saml_base_cfg_dir, 'secret-key.txt')):
            self.SECRET_KEY = open(os.path.join(_saml_base_cfg_dir, 'secret-key.txt')).read()
        else:
            pass

        # set SAML_PATH
        if 'NGX_SAML_AUTH_SAML_PATH' in os.environ:
            self.SAML_PATH = os.environ.get('NGX_SAML_AUTH_SAML_PATH')
        elif app_main_path and os.path.exists(os.path.join(app_main_path, 'instance', 'saml')):
            self.SAML_PATH = os.path.join(app_main_path, 'instance', 'saml')
        elif app_main_path and os.path.exists(os.path.join(app_main_path, 'saml')):
            self.SAML_PATH = os.path.join(app_main_path, 'saml')

class DevelopmentConfig(BaseConfig):
    '''
    Configuration for Development
    '''
    CONFIG_NAME = 'development'

    TESTING = False
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class ProductionConfig(BaseConfig):
    '''
    Configuration for Production
    '''
    CONFIG_NAME = 'production'

    TESTING = False
    DEBUG = False

class TestConfig(BaseConfig):
    '''
    Configuration for testing
    '''
    CONFIG_NAME = 'test'

    TESTING = True
    DEBUG = False

def create_config_obj(config_name):
    '''
    return a valid configuration 
    or a default configuration
    '''

    if config_name == 'development':
        return DevelopmentConfig()
    elif config_name == 'production':
        return ProductionConfig()
    elif config_name == 'test':
        return TestConfig()
    else:
        print("warning: config_name \"" + config_name + "\" not known ... using \"production\"")
        return ProductionConfig()

