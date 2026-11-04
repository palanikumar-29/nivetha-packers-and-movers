"""
URL configuration for nivetha_pm project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap
from core import views as core_views

admin_url = getattr(settings, 'ADMIN_URL', 'panel').strip('/') or 'panel'

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('', include('core.urls')),
    path(f'{admin_url}/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', core_views.robots_txt, name='robots_txt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
