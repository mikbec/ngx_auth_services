import logging
import click
from flask_babel import _

log = logging.getLogger(__name__)

def register_cli(app):
    @app.cli.command('list-routes', help="list used application routes and urls")
    def list_routes():
        click.echo(_("rule\tmethods\tendpoint"))
        click.echo(_("----\t-------\t--------"))
        for url in app.url_map.iter_rules():
            click.echo(_("%(r)s %(m)s %(e)s",
                         r=url.rule, m=url.methods, e=url.endpoint))

