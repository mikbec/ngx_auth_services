# Flask App configuration
This is for "default" environment ... please have a look at "app/config.py".

        cd /app/base/path
        source venv/bin/activate
        python main.py

You can use flask command too to start application like

        cd /app/base/path
        source venv/bin/activate
        export FLASK_APP=main.py
        #export FLASK_DEBUG=1
        export FLASK_ENV=development|production|test
        flask run

Additionally for complete available flask subcommands run

        flask --help

Before you can use the choosen environment you may have to initialize the database

        cd /app/base/path
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        flask db upgrade head
        (optional) chown -R www-data:www-data app.*.db
        flask list-routs

# UWSGI configuration
For uwsgi you may need a file `wsgi.py`

Start uwsgi by hand for example like this

        cd /app/base/path
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        ./venv/bin/uwsgi --socket 127.0.0.1:9080 --wsgi-file wsgi.py \
                         --callable app --processes 4 --threads 2 \
                         --uid awx --gid awx

You can put uwsgi commandline options in a config file f.e. `uwsgi.ini`

             [uwsgi]
             socket = 127.0.0.1:9080
             wsgi-file = wsgi.py
             callable = app
             processec = 4
             threads = 2
             uid = awx
             gid = awx

and start uwsgi with

        cd /app/base/path
        source venv/bin/activate
        export FLASK_APP=main.py
        export FLASK_ENV=development|production|test
        ./venv/bin/uwsgi uwsgi.ini

# Nginx configuration

