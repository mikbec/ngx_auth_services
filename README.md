# NGINX `auth_services`

- [NGINX `auth_services` `auth_saml` (for SAML)](#ngx-auth_services)
    - [Something to concern](#concern)
    - [Flask App configuration](#flask-app-config)
    - [uWSGI configuration](#uwsgi-config)
- [Services to control uWSGI](#uwsgi-controller-config)
    - [SUPERVISORD configuration](#supervisord-config)
    - [SYSTEMD configuration](#systemd-config)
- [NGINX configuration](#nginx-config)

# NGINX `auth_services` `auth_saml` (for SAML) {#ngx-auth_services}

## Something to concern {#concern}
This project provides a helper service for NGINX which will be called locally
via `ngx_auth_request` module to authenticate/authorize users.

At the moment it only works for SAML authentication, but should also be expandable
for other methods of authentication and/or authorization.

Service is written in Python and uses Flask. For SAML authentication it uses the
SAML Python Toolkit `python3-saml` provided by OneLogin. The `auth_saml` module
provided by this service is based on example code from `python3-saml/demo-flask/`
from OneLogin too.

## Flask App configuration {#flask-app-config}

For _development_ environment you can use the command `flask` to start application like

        cd /app/base/path/ngx_auth_services
        source venv/bin/activate
        export FLASK_APP=main.py
        #export FLASK_DEBUG=1
        export FLASK_ENV=development|production|test
        flask run

Additionally for complete available flask subcommands run

        flask --help

For _default_ (aka _production_) environment you should use a server that
implements the WSGI specification like for example `uWSGI`.

Before you can use the choosen environment you may have to initialize the database

        cd /app/base/path/ngx_auth_services
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        flask db upgrade head
        (optional) chown -R www-data:www-data app.*.db
        flask list-routes

## uWSGI configuration {#uwsgi-config}
For uWSGI you may need a file `wsgi.py`

You can start uwsgi by hand for example like this

        cd /app/base/path/ngx_auth_services
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        ./venv/bin/uwsgi --protocol=http --socket 127.0.0.1:5000 \
                         --wsgi-file wsgi.py --callable app \
                         --processes 4 --threads 2 --buffer-size = 65535 \
                         --uid www-data --gid www-data

You can put uwsgi commandline options in a config file f.e. `uwsgi.ini`

        [uwsgi]
        protocol = http
        socket = 127.0.0.1:5000
        wsgi-file = wsgi.py
        callable = app
        processes = 4
        threads = 2
        buffer-size = 65535
        # not needed if uwsgi runs under supervisord
        uid = www-data
        gid = www-data

and start uwsgi with

        cd /app/base/path/ngx_auth_services
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        ./venv/bin/uwsgi uwsgi.ini

# Services to control uWSGI {#uwsgi-controller-config}

## SUPERVISORD configuration {#supervisord-config}
Put a config file `ngx_auth_services.ini` with a content like this

        [program:ngx_auth_services]
        directory=/app/base/path/ngx_auth_services
        command=/app/base/path/ngx_auth_services/venv/bin/uwsgi uwsgi.ini
        stdout_logfile="syslog"
        stderr_logfile="syslog"
        startsecs=10
        user=www-data
        group=www-data
        stopsignal=QUIT
        stopasgroup=true
        killasgroup=true

into `/etc/supervisord.d/` and let it run with

        supervisorctl reload
        supervisorctl start ngx_auth_services 
        supervisorctl stop ngx_auth_services 
        supervisorctl status

## SYSTEMD configuration {#systemd-config}

todo

# NGINX configuration {#nginx-config}

todo
