"""
Local development settings.
"""
from .base import *

DEBUG = config('DEBUG', default=True, cast=bool)

