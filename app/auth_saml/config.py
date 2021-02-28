import os

from flask import session, url_for, current_app

from urllib.parse import urlparse
from flask_babel import _

from onelogin.saml2.errors import OneLogin_Saml2_Error, OneLogin_Saml2_ValidationError
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils

import yaml

# some internal configuration settings
_saml_base_cfg_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')
_saml_path_default_settings_filename = 'settings.json'
_saml_path_default_advanced_settings_filename = 'advanced_settings.json'
_auth_saml_default_cfg_filename = 'auth_saml.cfg'


class AuthSAMLConfig:
    AUTH_SAML_IDP_METADATA_URL = None
    AUTH_SAML_IDP_VALIDATE_CERT = True
    AUTH_SAML_IDP_ENTITY_ID = None

    # We name it "SAML_PATH" because Onelogin uses this config variable internally.
    SAML_PATH  = \
            os.environ.get('NGX_AUTH_SVCS_AUTH_SAML_PATH') or \
            _saml_base_cfg_dir
    AUTH_SAML_PATH_SETTINGS_AVAILABLE  = False

    AUTH_SAML_SETTINGS_DICT = {}

    AUTH_SAML_SP_X509CERT_FILE = None
    AUTH_SAML_SP_PRIVATEKEY_FILE = None
    AUTH_SAML_SP_NEW_X509CERT_FILE = None

    def set_SAML_IDP_METADATA_URL(self, url):
        self.AUTH_SAML_IDP_METADATA_URL = url

    def set_SETTINGS_DICT(self, settings_dict):
        self.AUTH_SAML_SETTINGS_DICT = settings_dict

    def update_config_obj(self, app_main_path=None):
        # set AUTH_SAML_IDP_METADATA_URL
        if 'NGX_AUTH_SVCS_AUTH_SAML_IDP_METADATA_URL' in os.environ:
            self.AUTH_SAML_IDP_METADATA_URL = os.environ.get('NGX_AUTH_SVCS_AUTH_SAML_IDP_METADATA_URL')
        elif 'SAML_IDP_METADATA_URL' in os.environ:
            self.AUTH_SAML_IDP_METADATA_URL = os.environ.get('SAML_IDP_METADATA_URL')

        # set SAML_PATH
        if ('NGX_AUTH_SVCS_AUTH_SAML_PATH' in os.environ) and \
                os.path.isdir(os.environ.get('NGX_AUTH_SVCS_AUTH_SAML_PATH')):
            self.SAML_PATH = os.environ.get('NGX_AUTH_SVCS_AUTH_SAML_PATH')
            self.AUTH_SAML_PATH_SETTINGS_AVAILABLE = \
                    are_saml_path_settings_available(os.environ.get('NGX_AUTH_SVCS_AUTH_SAML_PATH'))
        elif app_main_path and \
                os.path.isdir(os.path.join(app_main_path, 'instance', 'saml')):
            self.SAML_PATH = os.path.join(app_main_path, 'instance', 'saml')
            self.AUTH_SAML_PATH_SETTINGS_AVAILABLE = \
                    are_saml_path_settings_available(os.path.join(app_main_path, 'instance', 'saml'))
        elif app_main_path and \
                os.path.isdir(os.path.join(app_main_path, 'saml')):
            self.SAML_PATH = os.path.join(app_main_path, 'saml')
            self.AUTH_SAML_PATH_SETTINGS_AVAILABLE = \
                    are_saml_path_settings_available(os.path.join(app_main_path, 'saml'))
        elif _saml_base_cfg_dir and \
                os.path.isdir(os.path.join(_saml_base_cfg_dir, 'saml')):
            self.SAML_PATH = os.path.join(_saml_base_cfg_dir, 'saml')
            self.AUTH_SAML_PATH_SETTINGS_AVAILABLE = \
                    are_saml_path_settings_available(os.path.join(_saml_base_cfg_dir, 'saml'))
        else:
            self.AUTH_SAML_PATH_SETTINGS_AVAILABLE = False

    def create_auth_saml_setting(self, config_path, app):
        auth_saml_settings = {}
        if not config_path:
            return False
    
        config_filename = os.path.join(config_path, _auth_saml_default_cfg_filename)
        if not os.path.exists(config_filename):
            return False
    
        with open(config_filename, 'r') as stream:
            try:
                auth_saml_settings = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(_('Warning: Parsing of config file "{}" failed with exception.'.format(config_filename)))
                print(_('Warning: Exception was: {}'.format(str(exc))))
                if app:
                    app.logger.warning(_('Parsing of config file "{}" failed with exception.'.format(config_filename)))
                    app.logger.warning(_('Exception was: {}'.format(str(exc))))
                return False

        # Is there an "sp" section?
        if not auth_saml_settings['AUTH_SAML_SETTINGS'].get('sp', None):
             return False

        # enhance "sp" stuff if needed
        self.AUTH_SAML_SP_X509CERT_FILE = auth_saml_settings.get('AUTH_SAML_SP_X509CERT_FILE', None)
        self.AUTH_SAML_SP_PRIVATEKEY_FILE = auth_saml_settings.get('AUTH_SAML_SP_PRIVATEKEY_FILE', None)
        self.AUTH_SAML_SP_NEW_X509CERT_FILE = auth_saml_settings.get('AUTH_SAML_SP_NEW_X509CERT_FILE', None)
    
        # enhance "idp" stuff if needed
        self.AUTH_SAML_IDP_METADATA_URL = auth_saml_settings.get('AUTH_SAML_SP_X509CERT_FILE', None)
        self.AUTH_SAML_IDP_VALIDATE_CERT = set_string_to_boolean(auth_saml_settings.get('AUTH_SAML_IDP_VALIDATE_CERT', ""))
        self.AUTH_SAML_IDP_ENTITY_ID = set_empty_string_to_none(auth_saml_settings.get('AUTH_SAML_IDP_ENTITY_ID', None))

        # Is there an "idp" section?
        idp_data = {}
        if not auth_saml_settings['AUTH_SAML_SETTINGS'].get('idp', None):
            if auth_saml_settings.get('AUTH_SAML_IDP_METADATA_URL', None) and not self.AUTH_SAML_IDP_METADATA_URL:
                 self.AUTH_SAML_IDP_METADATA_URL = auth_saml_settings['AUTH_SAML_IDP_METADATA_URL']

            # try to get "idp" metadata
            idp_entity_id = self.AUTH_SAML_IDP_ENTITY_ID
            idp_validate_cert = None
            if self.AUTH_SAML_IDP_METADATA_URL:
                idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(
                        self.AUTH_SAML_IDP_METADATA_URL,
                        validate_cert=self.AUTH_SAML_IDP_VALIDATE_CERT,
                        entity_id=self.AUTH_SAML_IDP_ENTITY_ID)

        # set "idp" section if we got data for it
        if idp_data:
            auth_saml_settings['AUTH_SAML_SETTINGS']['idp'] = idp_data

        # now test and set settings
        try:
            settings = OneLogin_Saml2_Settings(settings=auth_saml_settings['AUTH_SAML_SETTINGS'], sp_validation_only=True)
        except (OneLogin_Saml2_Error, OneLogin_Saml2_ValidationError) as exc:
            print(_('Warning: Validation of SAML settings from config file "{}" failed with exception.'.format(config_filename)))
            print(_('Warning: Exception was: {}'.format(str(exc))))
            if app:
                app.logger.warning(_('Validation of SAML settings from config file "{}" failed with exception.'.format(config_filename)))
                app.logger.warning(_('Exception was: {}'.format(str(exc))))
            return False
    
        self.AUTH_SAML_SETTINGS_DICT = auth_saml_settings['AUTH_SAML_SETTINGS']
        return False

def are_saml_path_settings_available(saml_path):
    return os.path.exists(os.path.join(saml_path, _saml_path_default_settings_filename))

def are_saml_path_advanced_settings_available(saml_path):
    return os.path.exists(os.path.join(saml_path, _saml_path_default_advanced_settings_filename))

def set_empty_string_to_none(str_val=None):
    if not str_val:
        return None
    return str_val

def set_string_to_boolean(str_val=None):
    if not str_val:
        return False
    return str(str_val).lower() in ("yes", "true", "t", "1")

def create_config_obj(app=None):
    '''
    return a valid configuration 
    or a default configuration
    '''
    config_obj = AuthSAMLConfig()
    if not app:
        return config_obj

    if app.instance_path:
        config_obj.update_config_obj(app.instance_path)
    else:
        return config_obj

    config_obj.create_auth_saml_setting(app.instance_path, app)

    return config_obj
