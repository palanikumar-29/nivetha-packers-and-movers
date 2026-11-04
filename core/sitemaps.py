from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings


class StaticViewSitemap(Sitemap):
    """
    Sitemap listing only the five public pages, building absolute URLs from SITE_URL.
    """
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return [
            'core:home',
            'core:services',
            'core:gallery',
            'core:about',
            'core:contact',
        ]

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        urls = []
        for item in self.paginator.page(page).object_list:
            loc = f"{site_url}{self.location(item)}"
            priority = 1.0 if item == 'core:home' else self.priority
            url_info = {
                'item': item,
                'location': loc,
                'lastmod': None,
                'changefreq': self.changefreq,
                'priority': str(priority),
            }
            urls.append(url_info)
        return urls

