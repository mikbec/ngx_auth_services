import os

# some internal configuration settings
_default_secret_key = '!!! The python3-saml toolkit secret key you have to change! !!!'
_default_secret_key_filename = 'secret-key.txt'

class BaseConfig(object):
    '''
    The base class for configuration

    You should overwrite settings in sub classes.
    '''
    CONFIG_NAME = 'BaseConfig'

    INSTANCE_PATH = None

    SECRET_KEY = _default_secret_key
    SECRET_KEY_FILE = ''

    # URL_MASTER_CONTEXT must be empty or must begin and end with "/".
    URL_MASTER_CONTEXT = \
            os.environ.get('NGX_AUTH_SVCS_URL_MASTER_CONTEXT') or \
            '/auth_services/'

    def is_default_secret_key(self, test_secret_key=None):
        if test_secret_key:
            if test_secret_key == _default_secret_key:
                return True
        elif self.SECRET_KEY == _default_secret_key:
            return True
        return False

    def update_config_obj(self, app_main_path):
        # set INSTANCE_PATH
        if ('NGX_AUTH_SVCS_INSTANCE_PATH' in os.environ) and \
                os.path.isdir(os.environ.get('NGX_AUTH_SVCS_INSTANCE_PATH')):
            self.INSTANCE_PATH = os.environ.get('NGX_AUTH_SVCS_INSTANCE_PATH')

        # set SECRET_KEY
        if 'NGX_AUTH_SVCS_SECRET_KEY' in os.environ:
            self.SECRET_KEY = os.environ.get('NGX_AUTH_SVCS_SECRET_KEY')
        elif self.INSTANCE_PATH and \
                os.path.isfile(os.path.join(self.INSTANCE_PATH, _default_secret_key_filename)):
            self.SECRET_KEY = open(os.path.join(self.INSTANCE_PATH, _default_secret_key_filename)).read()
            self.SECRET_KEY_FILE = os.path.join(self.INSTANCE_PATH, _default_secret_key_filename)
        elif app_main_path and \
                os.path.isfile(os.path.join(app_main_path, 'instance', _default_secret_key_filename)):
            self.SECRET_KEY = open(os.path.join(app_main_path, 'instance', _default_secret_key_filename)).read()
            self.SECRET_KEY_FILE = os.path.join(app_main_path, 'instance', _default_secret_key_filename)
        elif app_main_path and \
                os.path.isfile(os.path.join(app_main_path, _default_secret_key_filename)):
            self.SECRET_KEY = open(os.path.join(app_main_path, _default_secret_key_filename)).read()
            self.SECRET_KEY_FILE = os.path.join(app_main_path, _default_secret_key_filename)
        else:
            pass

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

