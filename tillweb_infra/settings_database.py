# Access to till database

# By default we read the files 'database_name' and 'till_name' in the
# project root directory and set up tillweb in single-till read-only
# access mode.  If you want to do something different, replace the
# contents of this file.

from django.urls import reverse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

USING_DOCKER = os.getenv("USING_DOCKER", default="no") != "no"

TILLWEB_DATABASE_NAME = "emfcamp"

dbaccess = 'till:till@postgres:5432' if USING_DOCKER else ''

TILLWEB_SINGLE_SITE = True
TILLWEB_DATABASE = sessionmaker(
    bind=create_engine(
        f'postgresql+psycopg2://{dbaccess}/{TILLWEB_DATABASE_NAME}',
        pool_size=32, pool_recycle=600),
    info={'pubname': 'detail', 'reverse': reverse})
TILLWEB_PUBNAME = "Electromagnetic Field"
TILLWEB_LOGIN_REQUIRED = True
TILLWEB_DEFAULT_ACCESS = "M"
