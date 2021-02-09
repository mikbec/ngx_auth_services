import os
_saml_base_cfg_dir = os.path.abspath(os.path.dirname(__file__))
#_saml_base_cfg_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')

class BaseConfig(object):
    '''
    The base class for configuration

    You should overwrite settings in sub classes.
    '''
    SECRET_KEY = 'The python3-saml toolkit secret key you have to change!'
    SAML_PATH  = \
            os.environ.get('NGX_SAML_AUTH_SAML_PATH') or \
            _saml_base_cfg_dir

    # URL_MASTER_CONTEXT must be empty or must begin and end with "/".
    URL_MASTER_CONTEXT = \
            os.environ.get('NGX_SAML_AUTH_URL_MASTER_CONTEXT') or \
            '/auth_external/'

    @staticmethod
    def init_app(app):
        pass
  

class DevelopmentConfig(BaseConfig):
    '''
    Configuration for Development
    '''
    TESTING = False
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class ProductionConfig(BaseConfig):
    '''
    Configuration for Production
    '''
    TESTING = False
    DEBUG = False
    SECRET_KEY = 'init on instantiate'

    def init_app(app):
        self.SECRET_KEY = \
            os.environ.get('NGX_SAML_AUTH_SECRET_KEY') or \
            open(os.path.join(_saml_base_cfg_dir, 'secret-key.txt')).read()

class TestConfig(BaseConfig):
    '''
    Configuration for testing
    '''
    TESTING = True
    DEBUG = False
    SECRET_KEY = 'init on instantiate'

    def init_app(app):
        self.SECRET_KEY = \
            os.environ.get('NGX_SAML_AUTH_SECRET_KEY') or \
            open(os.path.join(_saml_base_cfg_dir, 'secret-test-key.txt')).read()

def get_config(config_name):
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
        return DevelopmentConfig()

