# NGINX `auth_services`

[TOC]

# NGINX `auth_services` `auth_saml`

## Something to concern
This project provides a helper service for NGINX which will be called locally
via `ngx_auth_request` module to authenticate/authorize users.

At the moment it only works for SAML authentication, but should also be expandable
for other methods of authentication and/or authorization.

Service is written in Python and uses Flask. For SAML authentication it uses the
SAML Python Toolkit `python3-saml` provided by OneLogin. The `auth_saml` module
provided by this service is based on example code from `python3-saml/demo-flask/`
from OneLogin too.

## Flask App configuration

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

Currently there is only one CLI command

        flask list-routes

to list urls (aka routes) that are being provided by the `ngx_auth_services`
application. 

## uWSGI configuration
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
        
        # not needed if uwsgi runs under supervisord or systemd
        uid = www-data
        gid = www-data
        
        # may be needed if uwsgi runs under systemd
        die-on-term = true

and start uwsgi with

        cd /app/base/path/ngx_auth_services
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        ./venv/bin/uwsgi --ini uwsgi.ini

# Services to control uWSGI

## SUPERVISORD configuration
Put a config file `ngx_auth_services.ini` with a content like this

        [program:ngx_auth_services]
        directory=/app/base/path/ngx_auth_services
        command=/app/base/path/ngx_auth_services/venv/bin/uwsgi --ini uwsgi.ini
        stdout_logfile="syslog"
        stderr_logfile="syslog"
        startsecs=10
        user=www-data
        group=www-data
        stopsignal=QUIT
        stopasgroup=true
        killasgroup=true
        environment=FLASK_APP=main.py,FLASK_ENV=production

into `/etc/supervisord.d/` and let it run with

        supervisorctl reload
        supervisorctl start ngx_auth_services 

To get some logging information try
        #supervisorctl stop ngx_auth_services 
        supervisorctl status

## SYSTEMD configuration

As an alternative to SUPERVISORD we can use SYSTEMD. For SYSTEMD service unit put a config
file `ngx_auth_services.service` with a content like this

        [Unit]
        Description=uWSGI instance to serve ngx_auth_services
        After=network-online.target
        Wants=network-online.target
        
        [Service]
        User=www-data
        Group=www-data
        WorkingDirectory=/app/base/path/ngx_auth_services
        Environment="FLASK_APP=main.py"
        Environment="FLASK_ENV=production"
        ExecStart=/app/base/path/ngx_auth_services/venv/bin/uwsgi --ini uwsgi.ini
        Restart=always
        RestartSec=10s
        KillSignal=SIGQUIT
        Type=notify
        StandardOutput=syslog
        StandardError=syslog
        NotifyAccess=all
        
        [Install]
        WantedBy=multi-user.target
        
into `/etc/system.d/system/` and let it run with

        systemctl daemon-reload
        systemctl start ngx_auth_services.service

To get some logging information try

        #systemctl stop ngx_auth_services.service
        systemctl status ngx_auth_services.service
        journalctl -f -u ngx_auth_services.service

# NGINX configuration

Here is a short virtual host configuration for nginx

        # NGINX config for centos 8 with
        # * auth_request
        # * uWSGI service ngx_auth_services reachable via http://127.0.0.1:5000
        # * and protected resource under /protected/ usable by PHP
        # * redirects all form http (port 80) to https (port 443)
        
        server {
            listen 80;
            listen [::]:80;
            server_name mysrv.mydom.zz;
        
            # enforce https
            return 301 https://$server_name:443$request_uri;
        }
        
        server {
            listen 443 ssl;
            listen [::]:443 ssl;
            server_name mysrv.mydom.zz;
        
            ssl_certificate        /etc/pki/tls/certs/mysrv.mydom.zz.crt;
            ssl_certificate_key    /etc/pki/tls/private/mysrv.mydom.zz.key;
            ssl_protocols          TLSv1.3 TLSv1.2;
            ssl_ciphers            EECDH+AESGCM:EDH+AESGCM;
            root  /var/www/mysrv.mydom.zz;
        
            # own logging
            error_log   /var/log/nginx/mysrv.mydom.zz-error.log;
            access_log  /var/log/nginx/mysrv.mydom.zz-access.log  main;
        
            # open access
            location / {
            }
        
            # protected resource
            location  /protected/ {
                # The sub-request to use
                auth_request /auth;
                # Specific login page to use
                error_page 401 = @error401;
        
                # Make the sub request data available
                #auth_request_set $authuser $upstream_http_as_x_username;       
                auth_request_set $authuser $upstream_http_as_x_uid;
                auth_request_set $authuser_c $upstream_http_as_x_uid_count;
                auth_request_set $groups $upstream_http_as_x_groups;
                auth_request_set $groups_c $upstream_http_as_x_groups_count;
        
                # Custom headers with authentication related data
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Remote-User $authuser;
        
                #include /etc/nginx/default.d/*.conf;
                index index.php index.html index.htm;
        
                location ~ \.(php|phar)(/.*)?$ {
                    fastcgi_split_path_info ^(.+\.(?:php|phar))(/.*)$;
        
                    fastcgi_intercept_errors on;
                    fastcgi_index  index.php;
                    include        fastcgi_params;
                    fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;
                    fastcgi_param  PATH_INFO $fastcgi_path_info;
        
                    fastcgi_param  REMOTE_USER $authuser;
                    fastcgi_param  REMOTE_USER_C $authuser_c;
                    fastcgi_param  REMOTE_GROUPS $groups;
                    fastcgi_param  REMOTE_GROUPS_C $groups_c;
        
                    fastcgi_pass   php-fpm;
                }
            }
        
            # auth_request location
            location = /auth {
                internal;
                # access to local authenticaten service
                proxy_pass http://127.0.0.1:5000/auth_services/auth_saml/auth_check;
        
                # no data is being transferred...
                proxy_pass_request_body off;
                proxy_set_header Content-Length "";
                proxy_set_header X-Origin-URI $request_uri;
        
                # Custom headers with authentication related data
                proxy_set_header Host $host;
                #proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded $request_uri;
        
                # Additional parameters to send to login page
                proxy_set_header X-My-Real-IP $remote_addr;
                proxy_set_header X-My-Real-Port $remote_port;
                proxy_set_header X-My-Server-Port $server_port;
            }
        
            # If the user is not logged in, redirect them to login URL
            location @error401 {
                # Login URL of SAML authentication
                return 302 https://mysrv.mydom.zz/auth_services/auth_saml/sso?url=https://$http_host$request_uri;
            }
        
            # Our local authentication service. 
            location /auth_services/ {
                # local authentication service
                proxy_pass http://127.0.0.1:5000;
            
                # Custom headers with authentication related data
                proxy_set_header Host $host;
                proxy_set_header X-Origin-URI $request_uri;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded $request_uri;
            
                # Additional parameters to send to login page
                proxy_set_header X-My-Real-IP $remote_addr;
                proxy_set_header X-My-Real-Port $remote_port;
                proxy_set_header X-My-Server-Port $server_port;
            }
        
            # open access to let IdP get our SAML metadata xml
            location /auth_services/auth_saml/metadata {
                proxy_pass http://127.0.0.1:5000;       # Where the metadata are.
                proxy_set_header X-My-Real-IP $remote_addr;
                proxy_set_header X-My-Real-Port $remote_port;
                proxy_set_header X-My-Server-Port $server_port;
            }
        }
