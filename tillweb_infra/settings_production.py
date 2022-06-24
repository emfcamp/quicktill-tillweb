# Django settings for production use

from .settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

STATIC_ROOT = BASE_DIR / "static"

ALLOWED_HOSTS = ['*']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
}
