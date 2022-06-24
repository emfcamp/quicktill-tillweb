EMF Till web service
====================

Infrastructure needed to bring up an instance of `quicktill.tillweb`,
plus the public-facing web pages for https://bar.emfcamp.org/

This is the EMF-specific fork of the project and contains assumptions
about how the EMF till is configured. [There is a separate repo for the generic version of the project here.](https://github.com/sde1000/quicktill-tillweb)

Setup for development
---------------------

Create a file `config/secret_key` containing a random secret:

```
mkdir -p config
python3 -c "import secrets; print(secrets.token_urlsafe())" >config/secret_key
```

Run `docker compose build` to build the development images, and
`docker compose up` to start the development web server. Once running,
you should be able to access the project at http://localhost:8000/

The development web server should pick up any changes you make
immediately. If you create a new migration, you'll need to stop and
restart manually to execute the migration.

Press Ctrl+C to stop the development web server.

To create a local superuser, run `docker compose run --rm app ./manage.py
createsuperuser`

To clean up afterwards, run `docker compose down --rmi local`

Updating dependencies
---------------------

If you update any dependencies in `pyproject.toml` you should run
`docker compose run --rm app poetry lock` to update the `poetry.lock`
file. This may take a long time because it will have to start from
scratch without a cache. If you have poetry installed in your
development environment, it may be faster to run `poetry lock`
directly.

Afer updating dependencies you should run `docker compose build` again
to rebuild the development images.

Developing without docker
-------------------------

To develop without docker you will need a local installation of
`poetry`, and a postgresql database called "emfcamp" with a till
database dump installed in it. You can find a suitable dump under
`docker/data/`.

Install dependencies: `poetry install`

Create a secret key as above.

Create/update the django database: `poetry run ./manage.py migrate`

Create a superuser: `poetry run ./manage.py createsuperuser`

Run the development server: `poetry run ./manage.py runserver`
