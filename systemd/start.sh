#!/bin/bash

export TILLWEB_VENV=$(poetry env info --path)
exec /usr/bin/uwsgi --ini=systemd/tillweb-uwsgi.conf
