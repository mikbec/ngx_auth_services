import os
from app import create_app
#from app import db
from app.cli import register_cli

app = create_app(os.getenv('FLASK_ENV') or 'default', __file__)

# register our cli commands
register_cli(app)

# for flask shell
@app.shell_context_processor
def make_shell_context():
#    return dict(db=db)
    return dict()

if __name__ == '__main__':
    app.run()
