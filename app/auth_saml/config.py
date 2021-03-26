import os

from flask import session, url_for, current_app

from urllib.parse import urlparse
from flask_babel import _

from onelogin.saml2.errors import OneLogin_Saml2_Error, OneLogin_Saml2_ValidationError
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils

import yaml

#from .views import index_acs, index_sls, metadata

# some internal configuration settings
_saml_base_cfg_dir =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')
_saml_path_default_settings_filename = 'settings.json'
_saml_path_default_advanced_settings_filename = 'advanced_settings.json'
_auth_saml_default_cfg_filename = 'auth_saml.cfg'


class AuthSAMLConfig:
    AUTH_SAML_CFG_FILENAME = None
    AUTH_SAML_IDP_METADATA_URL = None
    AUTH_SAML_IDP_VALIDATE_CERT = True
    AUTH_SAML_IDP_ENTITY_ID = None

    # We name it "SAML_PATH" because Onelogin uses this config variable internally.
    SAML_PATH  = \
            os.environ.get('NGX_AUTH_SVCS_AUTH_SAML_PATH') or \
            _saml_base_cfg_dir
    AUTH_SAML_PATH_SETTINGS_AVAILABLE  = False

    AUTH_SAML_SETTINGS_DICT = {}

    AUTH_SAML_SP_URL_PREFIX = None
    AUTH_SAML_SP_X509CERT_FILE = None
    AUTH_SAML_SP_PRIVATEKEY_FILE = None
    AUTH_SAML_SP_NEW_X509CERT_FILE = None

    AUTH_SAML_SP_SLO_URL = None

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
                #print(_('Warning: Parsing of config file "{}" failed with exception.'.format(config_filename)))
                #print(_('Warning: Exception was: {}'.format(str(exc))))
                if app:
                    app.logger.warning(_('Parsing of config file "{}" failed with exception.'.format(config_filename)))
                    app.logger.warning(_('Exception was: {}'.format(str(exc))))
                return False
        self.AUTH_SAML_CFG_FILENAME = config_filename

        # Is there an "AUTH_SAML_SETTINGS" section?
        if not auth_saml_settings.get('AUTH_SAML_SETTINGS', None):
            auth_saml_settings['AUTH_SAML_SETTINGS'] = {}
        # Is there an "sp" section?
        if not auth_saml_settings['AUTH_SAML_SETTINGS'].get('sp', None):
            auth_saml_settings['AUTH_SAML_SETTINGS']['sp'] = {}

        # enhance "sp" stuff if needed
        self.AUTH_SAML_SP_URL_PREFIX = auth_saml_settings.get('AUTH_SAML_SP_URL_PREFIX', None)
        self.AUTH_SAML_SP_X509CERT_FILE = auth_saml_settings.get('AUTH_SAML_SP_X509CERT_FILE', None)
        self.AUTH_SAML_SP_PRIVATEKEY_FILE = auth_saml_settings.get('AUTH_SAML_SP_PRIVATEKEY_FILE', None)
        self.AUTH_SAML_SP_NEW_X509CERT_FILE = auth_saml_settings.get('AUTH_SAML_SP_NEW_X509CERT_FILE', None)

        # load sp certificate from PEM file
        fn_sp_x509cert_file = None
        fn_sp_x509cert_line = None
        while self.AUTH_SAML_SP_X509CERT_FILE:
            # first try absolute
            filename = self.AUTH_SAML_SP_X509CERT_FILE
            if not os.path.exists(filename):
                filename = os.path.join(config_path, self.AUTH_SAML_SP_X509CERT_FILE)
            # if not found try relativ to config path
            if not os.path.exists(filename):
                #print(_('Warning: Configured AUTH_SAML_SP_X509CERT_FILE "{}" does not exist.'.format(self.AUTH_SAML_SP_X509CERT_FILE)))
                app.logger.warning(_('Warning: Configured AUTH_SAML_SP_X509CERT_FILE "{}" does not exist.'.format(self.AUTH_SAML_SP_X509CERT_FILE)))
                break
            # we got a file 
            fn_sp_x509cert_file = filename

            # now read it 
            x509cert_value = None
            with open(fn_sp_x509cert_file, 'r') as fp:
                x509cert_value =  "".join(line for line in fp)

            #print(_('Before: "{}"'.format(x509cert_value)))
            fn_sp_x509cert_line = OneLogin_Saml2_Utils.format_cert(x509cert_value, heads=False)
            #print(_('After:  "{}"'.format(fn_sp_x509cert_line)))
            break

        # load sp private key from PEM file
        fn_sp_privatekey_file = None
        fn_sp_privatekey_line = None
        while self.AUTH_SAML_SP_PRIVATEKEY_FILE:
            # first try absolute
            filename = self.AUTH_SAML_SP_PRIVATEKEY_FILE
            if not os.path.exists(filename):
                filename = os.path.join(config_path, self.AUTH_SAML_SP_PRIVATEKEY_FILE)
            # if not found try relativ to config path
            if not os.path.exists(filename):
                #print(_('Warning: Configured AUTH_SAML_SP_PRIVATEKEY_FILE "{}" does not exist.'.format(self.AUTH_SAML_SP_PRIVATEKEY_FILE)))
                app.logger.warning(_('Warning: Configured AUTH_SAML_SP_PRIVATEKEY_FILE "{}" does not exist.'.format(self.AUTH_SAML_SP_PRIVATEKEY_FILE)))
                break
            # we got a file 
            fn_sp_privatekey_file = filename

            # now read it 
            privatekey_value = None
            with open(fn_sp_privatekey_file, 'r') as fp:
                privatekey_value = "".join([line.strip().rstrip('\n').rstrip('\r') for line in fp])

            fn_sp_privatekey_line = OneLogin_Saml2_Utils.format_private_key(privatekey_value, heads=False)
            break

        # load sp new certificate from PEM file
        fn_sp_new_x509cert_file = None
        fn_sp_new_x509cert_line = None
        while self.AUTH_SAML_SP_NEW_X509CERT_FILE:
            # first try absolute
            filename = self.AUTH_SAML_SP_NEW_X509CERT_FILE
            if not os.path.exists(filename):
                filename = os.path.join(config_path, self.AUTH_SAML_SP_NEW_X509CERT_FILE)
            # if not found try relativ to config path
            if not os.path.exists(filename):
                #print(_('Warning: Configured AUTH_SAML_SP_NEW_X509CERT_FILE "{}" does not exist.'.format(self.AUTH_SAML_SP_NEW_X509CERT_FILE)))
                app.logger.warning(_('Warning: Configured AUTH_SAML_SP_NEW_X509CERT_FILE "{}" does not exist.'.format(self.AUTH_SAML_SP_NEW_X509CERT_FILE)))
                break
            # we got a file 
            fn_sp_new_x509cert_file = filename

            # now read it 
            new_x509cert_value = None
            with open(fn_sp_new_x509cert_file, 'r') as fp:
                new_x509cert_value = "".join([line.strip().rstrip('\n').rstrip('\r') for line in fp])

            fn_sp_new_x509cert_line = OneLogin_Saml2_Utils.format_cert(new_x509cert_value, heads=False)
            break

        # now set value(s)
        if fn_sp_x509cert_line:
            #print(_('Info: Using content of "{}" as x509cert of SP.'.format(fn_sp_x509cert_file)))
            app.logger.info(_('Info: Using content of "{}" as x509cert of SP.'.format(fn_sp_x509cert_file)))
            auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['x509cert'] = fn_sp_x509cert_line
            #print(_('auth_saml_settings:  "{}"'.format(auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['x509cert'])))
        if fn_sp_privatekey_line:
            #print(_('Info: Using content of "{}" as certificate private key of SP.'.format(fn_sp_privatekey_file)))
            app.logger.info(_('Info: Using content of "{}" as certificate private key of SP.'.format(fn_sp_privatekey_file)))
            auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['privateKey'] = fn_sp_privatekey_line
            #print(_('auth_saml_settings:  "{}"'.format(auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['privateKey'])))
        if fn_sp_new_x509cert_line:
            #print(_('Info: Using content of "{}" as new x509cert of SP.'.format(fn_sp_new_x509cert_file)))
            app.logger.info(_('Info: Using content of "{}" as new x509cert of SP.'.format(fn_sp_new_x509cert_file)))
            auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['x509certNew'] = fn_sp_new_x509cert_line
            #print(_('auth_saml_settings:  "{}"'.format(auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['x509certNew'])))

        # run settings check now or later?
        defer_settings_check = False

        # set entityId => "http.../metadata"
        if not auth_saml_settings['AUTH_SAML_SETTINGS']['sp'].get('entityId', None):
            #print(_('Info: SP entityId not set ... do it later'))
            app.logger.info(_('SP entityId not set ... do it later'))
            defer_settings_check = True

        # set singleLogoutService => "http.../sls"
        if not auth_saml_settings['AUTH_SAML_SETTINGS']['sp'].get('singleLogoutService', None):
            #print(_('Info: SP singleLogoutService not set ... do it later'))
            app.logger.info(_('SP singleLogoutService not set ... do it later'))
            defer_settings_check = True
        elif not auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['singleLogoutService'].get('url', None):
            #print(_('Info: SP singleLogoutService/url not set ... do it later'))
            app.logger.info(_('SP singleLogoutService/url not set ... do it later'))
            defer_settings_check = True

        # set assertionConsumerService/url => "http.../acs"
        if not auth_saml_settings['AUTH_SAML_SETTINGS']['sp'].get('assertionConsumerService', None):
            #print(_('Info: SP assertionConsumerService not set ... do it later'))
            app.logger.info(_('SP assertionConsumerService not set ... do it later'))
            defer_settings_check = True
        elif not auth_saml_settings['AUTH_SAML_SETTINGS']['sp']['assertionConsumerService'].get('url', None):
            #print(_('Info: SP assertionConsumerService/url not set ... do it later'))
            app.logger.info(_('SP assertionConsumerService/url not set ... do it later'))
            defer_settings_check = True

        # enhance "idp" stuff if needed
        self.AUTH_SAML_IDP_METADATA_URL = auth_saml_settings.get('AUTH_SAML_IDP_METADATA_URL', None)
        self.AUTH_SAML_IDP_VALIDATE_CERT = set_string_to_boolean(auth_saml_settings.get('AUTH_SAML_IDP_VALIDATE_CERT', "True"))
        self.AUTH_SAML_IDP_ENTITY_ID = set_empty_string_to_none(auth_saml_settings.get('AUTH_SAML_IDP_ENTITY_ID', None))

        # Is there an "idp" section?
        idp_data = {}
        if not auth_saml_settings['AUTH_SAML_SETTINGS'].get('idp', None):
            if auth_saml_settings.get('AUTH_SAML_IDP_METADATA_URL', None) and not self.AUTH_SAML_IDP_METADATA_URL:
                 self.AUTH_SAML_IDP_METADATA_URL = auth_saml_settings.get('AUTH_SAML_IDP_METADATA_URL')

            # try to get "idp" metadata
            idp_metadata_url = self.AUTH_SAML_IDP_METADATA_URL
            idp_validate_cert = self.AUTH_SAML_IDP_VALIDATE_CERT
            idp_entity_id = self.AUTH_SAML_IDP_ENTITY_ID
            if idp_metadata_url:
                app.logger.info(_('Try to get IDP data from: idp_metadata_url="{}" idp_validate_cert="{}" idp_entity_id="{}"'.format(\
                        idp_metadata_url, idp_validate_cert, idp_entity_id)))
                idp_data = OneLogin_Saml2_IdPMetadataParser.parse_remote(\
                        url=idp_metadata_url, \
                        validate_cert=idp_validate_cert, \
                        entity_id=idp_entity_id)

        # set "idp" section if we got data for it
        if idp_data and idp_data.get('idp', None):
            auth_saml_settings['AUTH_SAML_SETTINGS']['idp'] = idp_data['idp']

        # now test and set settings (if not defer at later time)
        if defer_settings_check:
            #print(_('Info: Validation of SAML settings from config file "{}" defered at later.'.format(config_filename)))
            app.logger.info(_('Validation of SAML settings from config file "{}" defered at later.'.format(config_filename)))
        else:
            try:
                #settings = OneLogin_Saml2_Settings(settings=auth_saml_settings['AUTH_SAML_SETTINGS'], sp_validation_only=True)
                settings = OneLogin_Saml2_Settings(settings=auth_saml_settings['AUTH_SAML_SETTINGS'])
            except (OneLogin_Saml2_Error, OneLogin_Saml2_ValidationError) as exc:
                #print(_('Warning: Validation of SAML settings from config file "{}" failed with exception.'.format(config_filename)))
                #print(_('Warning: Exception was: {}'.format(str(exc))))
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

def set_sp_metadata_urls():

    # run settings check now if we set some data?
    run_settings_check = False
    sp_url_prefix = current_app.config.get('AUTH_SAML_SP_URL_PREFIX', None)

    # first set URL for logout (slo)
    if not current_app.config.get('AUTH_SAML_SP_SLO_URL', None):
        if sp_url_prefix:
            url = sp_url_prefix + url_for('auth_saml.index_slo')
        else:
            url = url_for('auth_saml.index_slo', _external=True)
        current_app.config['AUTH_SAML_SP_SLO_URL'] = url

    # set entityId => "http.../metadata/"
    if not current_app.config['AUTH_SAML_SETTINGS_DICT']['sp'].get('entityId', None):
        if sp_url_prefix:
            url = sp_url_prefix + url_for('auth_saml.metadata')
        else:
            url = url_for('auth_saml.metadata', _external=True)
        #print(_('Info: Defered set SP entityId => "{}"'.format(url)))
        current_app.logger.info(_('Defered set SP entityId => "{}"'.format(url)))
        current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['entityId'] = url
        run_settings_check = True

    # set singleLogoutService => "http.../sls"
    set_sls = False
    set_sls_url = False
    if not current_app.config['AUTH_SAML_SETTINGS_DICT']['sp'].get('singleLogoutService', None):
        set_sls = True
    elif not current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['singleLogoutService'].get('url', None):
        set_sls_url = True
    if set_sls or set_sls_url:
        if sp_url_prefix:
            url = sp_url_prefix + url_for('auth_saml.index_sls')
        else:
            url = url_for('auth_saml.index_sls', _external=True)
        #print(_('Info: Defered set SP singleLogoutService/url => "{}"'.format(url)))
        current_app.logger.info(_('Defered set SP singleLogoutService/url => "{}"'.format(url)))
        if set_sls:
            current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['singleLogoutService'] = {}
        current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['singleLogoutService']['url'] = url
        run_settings_check = True

    # set assertionConsumerService/url => "http.../acs"
    set_acs = False
    set_acs_url = False
    if not current_app.config['AUTH_SAML_SETTINGS_DICT']['sp'].get('assertionConsumerService', None):
        set_acs = True
    elif not current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['assertionConsumerService'].get('url', None):
        set_acs_url = True
    if set_acs or set_acs_url:
        if sp_url_prefix:
            url = sp_url_prefix + url_for('auth_saml.index_acs')
        else:
            url = url_for('auth_saml.index_acs', _external=True)
        #print(_('Info: Defered set SP assertionConsumerService/url => "{}"'.format(url)))
        current_app.logger.info(_('Defered set SP assertionConsumerService/url => "{}"'.format(url)))
        if set_acs:
            current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['assertionConsumerService'] = {}
        current_app.config['AUTH_SAML_SETTINGS_DICT']['sp']['assertionConsumerService']['url'] = url
        run_settings_check = True

    # now test our settings
    if run_settings_check:
        config_filename = current_app.config.get('AUTH_SAML_CFG_FILENAME', 'auth_saml_cfg_filename not set')
        try:
            #settings = OneLogin_Saml2_Settings(settings=current_app.config['AUTH_SAML_SETTINGS_DICT'], sp_validation_only=True)
            settings = OneLogin_Saml2_Settings(settings=current_app.config['AUTH_SAML_SETTINGS_DICT'])
        except (OneLogin_Saml2_Error, OneLogin_Saml2_ValidationError) as exc:
            #print(_('Warning: Defered validation of SAML settings from config file "{}" failed with exception.'.format(config_filename)))
            #print(_('Warning: Exception was: {}'.format(str(exc))))
            current_app.logger.warning(_('Defered validation of SAML settings from config file "{}" failed with exception.'.format(config_filename)))
            current_app.logger.warning(_('Exception was: {}'.format(str(exc))))
            return
    return 
