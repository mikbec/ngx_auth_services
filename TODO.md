TODOs
-----

* Migration to instance path for configuration.
* In main.py we should use `create_app(..., __file__)` to configure application.
* Use something like INI- or YAML-Format to configure `app.from_cfg_file('config.cfg')`.
* For Metadata XML use external server name and `url_for(..., _external=True)`.
* Do configuration of `settings.json` and `advanced_settings.json` via config file.
  Or put these files with its `saml/` path into instance path.
* Print out settings in log file on application start.
