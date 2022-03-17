EMF Till web service
====================

Minimal infrastructure needed to bring up an instance of
`quicktill.tillweb` as a uwsgi service.

This is the EMF-specific fork of the project and contains assumptions
about how the EMF till is configured. [There is a separate repo for the generic version of the project here.](https://github.com/sde1000/quicktill-tillweb)

Setup for development
---------------------

First install [quicktill](https://github.com/sde1000/quicktill) and
follow the quick start instructions to create the emfcamp database
using the 2018 test dataset.

To configure, create a file `secret_key` containing a random secret, a
python3 virtualenv called `venv` and install all the requirements from
`requirements.txt` in it:

```
python3 -c "import secrets; print(secrets.token_urlsafe())" >secret_key
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

(N.B. this leaves your shell using the venv you have just created. To
exit the venv, type `deactivate`. To enter the venv again, type
`source venv/bin/activate`.)

You will need to `export PYTHONPATH=/path/to/quicktill` to use an
unpacked copy of the `quicktill` repo. It isn't possible to install
`quicktill` through `pip` at the moment.

While in the venv, run `./manage.py migrate` to create the Django
database, and `./manage.py createsuperuser` to create an initial admin
user.

At this point you should be able to run `./start-testserver` to start
a webserver on localhost:8000 to test the installation.

Setup for deployment
--------------------

Similar to setup for development, but specify
`"--system-site-packages"` to `virtualenv` when creating the venv and
you may need to sort out dependencies manually when installing
required packages, if some of the requirements turn out to be older
than those already installed.

Installation
------------

As root, copy `tillweb-nginx-configuration` to
`/etc/nginx/sites-available/tillweb` and edit it as appropriate.

Delete /etc/nginx/sites-enabled/default and symlink
/etc/nginx/sites-available/tillweb to /etc/nginx/sites-enabled/tillweb

Arrange for `./start-daemon` to be run at boot to start uwsgi serving
the website.  You may need to arrange for quicktill to be on the
PYTHONPATH if it isn't in the virtualenv.

If your system is running systemd, you can use a systemd user unit to
start uwsgi.

You must run `loginctl enable-linger your-username` once, to enable
the service to run while you are not logged in.  (Otherwise it will
start automatically when you log in and stop when you log out.)

Copy systemd/tillweb.service to ~/.config/systemd/user/,
edit if necessary to set PYTHONPATH, and enable it:

```
mkdir -p ~/.config/systemd/user
cp systemd/tillweb.service ~/.config/systemd/user/
sensible-editor ~/.config/systemd/user/tillweb.service
systemctl --user enable tillweb.service
systemctl --user start tillweb.service
```
