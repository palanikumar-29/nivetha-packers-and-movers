"""
Production settings for Render deployment.
"""
from .base import *

DEBUG = False

SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'

# CSRF Trusted Origins for HTTPS on Render / custom domains
raw_csrf = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = raw_csrf
else:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{host.lstrip('.')}"
        for host in ALLOWED_HOSTS
        if host not in ('localhost', '127.0.0.1', 'testserver', '*')
    ]

