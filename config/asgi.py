"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from kit.conf import initialize_conf

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

initialize_conf()

application = get_asgi_application()
