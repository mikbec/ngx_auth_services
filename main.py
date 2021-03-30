import os
from app import create_app, do_it_before_first_request
#from app import db
from app.cli import register_cli

app = create_app(os.environ.get('FLASK_ENV', 'default'), __file__)

# register our cli commands
register_cli(app)

# register to run once before any request
@app.before_first_request
def do_it_bfr():
    do_it_before_first_request()

# for flask shell
@app.shell_context_processor
def make_shell_context():
#    return dict(db=db)
    return dict()

if __name__ == '__main__':
    app.run()
