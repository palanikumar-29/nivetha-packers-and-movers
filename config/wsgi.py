"""
WSGI config for nivetha_pm project.

Defaults to production settings so WSGI servers (e.g. gunicorn on Render)
never run with local settings (DEBUG=True) by accident.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()

