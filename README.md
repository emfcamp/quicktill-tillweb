EMF Till web service
====================

Minimal infrastructure needed to bring up an instance of
`quicktill.tillweb` as a uwsgi service.

This is the EMF-specific fork of the project and contains assumptions
about how the EMF till is configured. [There is a separate repo for the generic version of the project here.](https://github.com/sde1000/quicktill-tillweb)

Setup for development
---------------------

Ensure you have [poetry](https://python-poetry.org/)
installed. Installation instructions are on
[this page](https://python-poetry.org/docs/master/).

First install [quicktill](https://github.com/sde1000/quicktill) and
follow the quick start instructions to create the emfcamp database
using the 2018 test dataset.

Install the project dependencies:

```
poetry install
```

To configure, create a file `secret_key` containing a random secret:

```
python3 -c "import secrets; print(secrets.token_urlsafe())" >secret_key
```

Create the Django database and an initial admin user:

```
poetry run ./manage.py migrate
poetry run ./manage.py createsuperuser
```

To start a web server on http://localhost:8000/ to test the service:
```
poetry run ./manage.py runserver
```

Installation
------------

As root:

* copy `tillweb-nginx-configuration` to `/etc/nginx/sites-available/tillweb`
and edit it as appropriate.
* delete `/etc/nginx/sites-enabled/default` and symlink
`/etc/nginx/sites-available/tillweb` to `/etc/nginx/sites-enabled/tillweb`
* run `loginctl enable-linger your-username` to enable the service to run
while you are not logged in

As the user that will run the service:

Copy `systemd/tillweb.service` to `~/.config/systemd/user/` and enable it:

```
mkdir -p ~/.config/systemd/user
cp systemd/tillweb.service ~/.config/systemd/user/
systemctl --user enable tillweb.service
systemctl --user start tillweb.service
```

Outside of the scope of these instructions: set up DNS entries and
letsencrypt so you can access the service over https.
