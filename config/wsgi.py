"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from kit.conf import initialize_conf

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

initialize_conf()

application = get_wsgi_application()
