TODOs
-----

* Print out settings in log file on application start.
* Remove additional "attrs" pages because it is not needed anymore.
* Describe usage of SLO URL.
* Provide SUPERVISORD example config.
* Provide NGINX example config.
* Describe variable translation from header variables to `upstream_http_*`
  variables.
* Provide complete example config with test web pages.
* Write consistent documentation.

DONE
----
[2021-03-30 20:08:56 +02:00]

* let defered init do in `@app.before_first_request`
* Implement decision for `lowercase_urlencoding` in `prepare_flask_request()`
  in file views.py because Defaults to false. But ADFS users should set this to
  true.

    * Now you can set it in `instance/auth_saml.cfg` as option
      `AUTH_SAML_IDP_LC_URLENC` which is of type boolean.

[2021-03-25 12:56:10 +01:00]

* Use something like INI- or YAML-Format to configure `app.from_cfg_file('config.cfg')`.

    * Now configuration will be done via configuration file in YAML format.
    * Name of config file is `instance/auth_saml.cfg`

* Do configuration of `settings.json` and `advanced_settings.json` via config file.
  Or put these files with its `saml/` path into instance path.

    * Now these two files are configurable via section "`AUTH_SAML_SETTINGS`".

* For Metadata XML use external server name and `url_for(..., _external=True)`.

    * Generation of Metadata XML of SP now can be done automatically and can be
      influenced by a few variables.

[2021-02-23 12:06:32 +01:00]

* Migration to instance path for configuration.
* In main.py we should use `create_app(..., __file__)` to configure application.
