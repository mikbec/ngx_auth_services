from flask import request, render_template, redirect, session, \
                  make_response, url_for, flash, current_app
from urllib.parse import urlparse
from flask_babel import _
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

# auth_saml stuff
from .tools import nocache
from . import bp as auth_saml_bp

# for current_app.logger
import pprint

def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=current_app.config['SAML_PATH'])
    return auth


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        #'https': 'on' if request.scheme == 'https' else 'off',
        'https': 'on',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'post_data': request.form.copy()
    }

@auth_saml_bp.route('/', methods=['GET', 'POST'])
def index():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    #hdrs = dict(request.headers)
    #current_app.logger.info('Info(/): Got header: '+pprint.pformat(hdrs))
    #current_app.logger.info('Info(/): Got req : '+pprint.pformat(req))
    #current_app.logger.info('Info(/): Got args: '+pprint.pformat(request.args))

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    current_app.logger.info('Info(/)->out: render_template(index.html)')
    return render_template(
                'auth_saml/index.html',
                errors=errors,
                error_reason=error_reason,
                not_auth_warn=not_auth_warn,
                success_slo=success_slo,
                attributes=attributes,
                paint_logout=paint_logout
            )

def do_index_sso(url_for_arg):
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    hdrs = dict(request.headers)
    current_app.logger.info('Info(/sso): Got header: '+pprint.pformat(hdrs))
    current_app.logger.info('Info(/sso): Got req : '+pprint.pformat(req))
    current_app.logger.info('Info(/sso): Got args: '+pprint.pformat(request.args))

    return_to = url_for(url_for_arg)
    if 'url' in request.args:
        return_to = request.args['url']
    #return redirect(return_to)
    # If AuthNRequest ID need to be stored in order to later validate it, do instead
    sso_built_url = auth.login(return_to)
    session['AuthNRequestID'] = auth.get_last_request_id()
    current_app.logger.info('Info(/sso)->out: redirect(sso_built_url): ' + sso_built_url)
    return redirect(sso_built_url)

@auth_saml_bp.route('/sso', methods=['GET', 'POST'])
@nocache
def index_sso():
    return(do_index_sso('.index'))

@auth_saml_bp.route('/sso2', methods=['GET', 'POST'])
@nocache
def index_sso2():
    return(do_index_sso('.attrs'))

@auth_saml_bp.route('/slo', methods=['GET', 'POST'])
@nocache
def index_slo():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    #hdrs = dict(request.headers)
    #current_app.logger.info('Info(/slo): Got header: '+pprint.pformat(hdrs))
    #current_app.logger.info('Info(/slo): Got req : '+pprint.pformat(req))
    #current_app.logger.info('Info(/slo): Got args: '+pprint.pformat(request.args))

    name_id = session_index = name_id_format = name_id_nq = name_id_spnq = None
    if 'samlNameId' in session:
        name_id = session['samlNameId']
    if 'samlSessionIndex' in session:
        session_index = session['samlSessionIndex']
    if 'samlNameIdFormat' in session:
        name_id_format = session['samlNameIdFormat']
    if 'samlNameIdNameQualifier' in session:
        name_id_nq = session['samlNameIdNameQualifier']
    if 'samlNameIdSPNameQualifier' in session:
        name_id_spnq = session['samlNameIdSPNameQualifier']

    current_app.logger.info('Info(/slo)->out: redirect(auth.logout)')
    return redirect(auth.logout(name_id=name_id,
                       session_index=session_index,
                       nq=name_id_nq,
                       name_id_format=name_id_format,
                       spnq=name_id_spnq))

@auth_saml_bp.route('/acs', methods=['GET', 'POST'])
@nocache
def index_acs():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    #hdrs = dict(request.headers)
    #current_app.logger.info('Info(/acs): Got header: '+pprint.pformat(hdrs))
    #current_app.logger.info('Info(/acs): Got req : '+pprint.pformat(req))
    #current_app.logger.info('Info(/acs): Got args: '+pprint.pformat(request.args))

    request_id = None
    if 'AuthNRequestID' in session:
        request_id = session['AuthNRequestID']

    auth.process_response(request_id=request_id)
    errors = auth.get_errors()
    not_auth_warn = not auth.is_authenticated()
    if len(errors) == 0:
        if 'AuthNRequestID' in session:
            del session['AuthNRequestID']
        session['samlUserdata'] = auth.get_attributes()
        session['samlNameId'] = auth.get_nameid()
        session['samlNameIdFormat'] = auth.get_nameid_format()
        session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
        session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
        session['samlSessionIndex'] = auth.get_session_index()
        self_url = OneLogin_Saml2_Utils.get_self_url(req)
        if 'RelayState' in request.form and self_url != request.form['RelayState']:
            current_app.logger.info('Info(/acs)->out: Got RelayState: '+pprint.pformat(request.form['RelayState']))
            return redirect(auth.redirect_to(request.form['RelayState']))
    elif auth.get_settings().is_debug_active():
        error_reason = auth.get_last_error_reason()

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    current_app.logger.info('Info(/acs)->out: render_template(auth_saml/index.html)')
    return render_template(
                'auth_saml/index.html',
                errors=errors,
                error_reason=error_reason,
                not_auth_warn=not_auth_warn,
                success_slo=success_slo,
                attributes=attributes,
                paint_logout=paint_logout
            )

@auth_saml_bp.route('/sls', methods=['GET', 'POST'])
@nocache
def index_sls():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    #hdrs = dict(request.headers)
    #current_app.logger.info('Info(/sls): Got header: '+pprint.pformat(hdrs))
    #current_app.logger.info('Info(/sls): Got req : '+pprint.pformat(req))
    #current_app.logger.info('Info(/sls): /sls Got args: '+pprint.pformat(request.args))

    request_id = None
    if 'LogoutRequestID' in session:
        request_id = session['LogoutRequestID']
    dscb = lambda: session.clear()
    url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
    errors = auth.get_errors()
    if len(errors) == 0:
        if url is not None:
            current_app.logger.info('Info(/sls)->out: sls out via redirect url: ' + url)
            return redirect(url)
        else:
            flash('User successfully logged out.', 'info')
            success_slo = True
    elif auth.get_settings().is_debug_active():
        error_reason = auth.get_last_error_reason()

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    if 'SAMLResponse' in request.args:
        current_app.logger.info('Info(/sls)->out: redirect(.index)')
        return redirect(url_for('.index'))

    current_app.logger.info('Info(/sls)->out: render_template(auth_saml/index.html)')
    return render_template(
                'auth_saml/index.html',
                errors=errors,
                error_reason=error_reason,
                not_auth_warn=not_auth_warn,
                success_slo=success_slo,
                attributes=attributes,
                paint_logout=paint_logout
            )

@auth_saml_bp.route('/attrs/')
@nocache
def attrs():
    paint_logout = False
    attributes = False

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    current_app.logger.info('Info(/attrs)->out: render_template(auth_saml/attrs.html)')
    return render_template(
                'auth_saml/attrs.html',
                paint_logout=paint_logout,
                attributes=attributes
            )


@auth_saml_bp.route('/metadata/')
@nocache
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        response = make_response(metadata, 200)
        response.headers['Content-Type'] = 'text/xml'
    else:
        response = make_response(', '.join(errors), 500)
    return response

@auth_saml_bp.route('/auth_check', methods=['GET', 'POST'])
@nocache
def auth_check():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    paint_logout = False
    attributes = False
    out_code = 200

    hdrs = dict(request.headers)
    current_app.logger.info('Info(/auth_check): Got header: '+pprint.pformat(hdrs))
    current_app.logger.info('Info(/auth_check): Got req : '+pprint.pformat(req))
    current_app.logger.info('Info(/auth_check): Got args: '+pprint.pformat(request.args))

    #if not auth.is_authenticated():
    #    response = make_response('User authentication needed.', 401)
    #    current_app.logger.info('Info(/auth_check)->out: out via 401')
    #    return response

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()
        out_code = 200
    else:
        # not authenticated
        out_code = 401

    response = make_response(
                 render_template(
                     'auth_saml/auth_check.html',
                     paint_logout=paint_logout,
                     attributes=attributes
                 ), out_code)

    if attributes:
        #current_app.logger.info('Info(/auth_check): Got '+str(len(attributes))+' attributes: '+pprint.pformat(attributes))
        for key, value in attributes:
            current_app.logger.info('Info(/auth_check): Got attributes['+key+']: '+pprint.pformat(value))
            response.headers['X-ATTR-'+key] = value[0]
            if len(value) > 1:
                for i in range(len(value)):
                    response.headers['X-ATTR-'+key+'-'+str(i)] = value[i]


    current_app.logger.info('Info(/auth_check)->out: out via '+str(out_code))
    return response

