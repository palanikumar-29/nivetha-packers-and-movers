import json
import re
from django.test import TestCase, override_settings
from django.urls import reverse


class SeoInfrastructureTest(TestCase):
    """
    Story 1.6: SEO Infrastructure tests covering sitemap.xml, robots.txt,
    JSON-LD structured data, metadata constraints, and 404 noindex robots.
    """

    def test_sitemap_returns_http_200_and_lists_five_pages(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        content = response.content.decode()

        self.assertIn('<loc>http://localhost:8000/</loc>', content)
        self.assertIn('<loc>http://localhost:8000/services/</loc>', content)
        self.assertIn('<loc>http://localhost:8000/gallery/</loc>', content)
        self.assertIn('<loc>http://localhost:8000/about/</loc>', content)
        self.assertIn('<loc>http://localhost:8000/contact/</loc>', content)
        self.assertNotIn('/panel/', content)
        self.assertNotIn('/admin/', content)

        # Count total <loc> tags in sitemap - exactly 5
        loc_count = len(re.findall(r'<loc>', content))
        self.assertEqual(loc_count, 5)

    @override_settings(SITE_URL='https://nivethapackers.in')
    def test_sitemap_respects_custom_site_url(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn('<loc>https://nivethapackers.in/</loc>', content)
        self.assertIn('<loc>https://nivethapackers.in/services/</loc>', content)
        self.assertNotIn('localhost:8000', content)

    def test_robots_txt_format_and_disallow_admin(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        content = response.content.decode()

        self.assertIn('User-agent: *', content)
        self.assertIn('Allow: /', content)
        self.assertIn('Disallow: /panel/', content)
        self.assertIn('Sitemap: http://localhost:8000/sitemap.xml', content)

    @override_settings(ADMIN_URL='secret-owner-portal', SITE_URL='https://nivethapackers.in')
    def test_robots_txt_reflects_admin_url_and_site_url_settings(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn('Disallow: /secret-owner-portal/', content)
        self.assertNotIn('Disallow: /panel/', content)
        self.assertIn('Sitemap: https://nivethapackers.in/sitemap.xml', content)

    @override_settings(BUSINESS_PHONE='+91 98765 43210', BUSINESS_ADDRESS='Tiruppur, Tamil Nadu')
    def test_json_ld_valid_schema_and_expected_fields(self):
        pages = ['core:home', 'core:services', 'core:gallery', 'core:about', 'core:contact']
        for page_name in pages:
            response = self.client.get(reverse(page_name))
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()

            # Find JSON-LD script and assert it is strictly non-empty
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
            self.assertIsNotNone(match, f"Missing ld+json script tag on {page_name}")
            raw_json = match.group(1).strip()
            self.assertTrue(len(raw_json) > 0, f"ld+json script block is empty on {page_name}")

            schema = json.loads(raw_json)
            self.assertEqual(schema.get('@context'), 'https://schema.org')
            self.assertEqual(schema.get('@type'), 'MovingCompany')
            self.assertEqual(schema.get('name'), 'Nivetha Packers and Movers')
            self.assertEqual(schema.get('url'), 'http://localhost:8000')
            self.assertEqual(schema.get('telephone'), '+91 98765 43210')
            self.assertEqual(schema.get('areaServed'), ['Tiruppur', 'Chennai', 'Madurai'])

            # Verify address structure
            self.assertIsInstance(schema.get('address'), dict)
            self.assertEqual(schema['address'].get('@type'), 'PostalAddress')
            self.assertEqual(schema['address'].get('addressLocality'), 'Tiruppur')
            self.assertEqual(schema['address'].get('addressRegion'), 'Tamil Nadu')
            self.assertEqual(schema['address'].get('addressCountry'), 'IN')

            # Verify strictly NO unconfirmed / forbidden fields
            forbidden_fields = ['aggregateRating', 'reviews', 'openingHours', 'priceRange', 'foundingDate']
            for field in forbidden_fields:
                self.assertNotIn(field, schema, f"Forbidden field '{field}' found on {page_name}")

    @override_settings(BUSINESS_PHONE='')
    def test_json_ld_omits_telephone_when_empty(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
        self.assertIsNotNone(match)
        raw_json = match.group(1).strip()
        self.assertTrue(len(raw_json) > 0)
        schema = json.loads(raw_json)
        self.assertNotIn('telephone', schema)

    @override_settings(SITE_URL='https://nivethapackers.in')
    def test_json_ld_reflects_site_url(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
        self.assertIsNotNone(match)
        raw_json = match.group(1).strip()
        self.assertTrue(len(raw_json) > 0)
        schema = json.loads(raw_json)
        self.assertEqual(schema['url'], 'https://nivethapackers.in')

    def test_open_graph_and_twitter_tags_present_with_real_values(self):
        pages = ['core:home', 'core:services', 'core:gallery', 'core:about', 'core:contact']
        for page_name in pages:
            response = self.client.get(reverse(page_name))
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()

            og_title = re.search(r'<meta property="og:title" content="(.*?)">', content)
            self.assertIsNotNone(og_title, f"Missing og:title on {page_name}")
            self.assertTrue(bool(og_title.group(1).strip()), f"Empty og:title on {page_name}")

            og_desc = re.search(r'<meta property="og:description" content="(.*?)">', content)
            self.assertIsNotNone(og_desc, f"Missing og:description on {page_name}")
            self.assertTrue(bool(og_desc.group(1).strip()), f"Empty og:description on {page_name}")

            og_type = re.search(r'<meta property="og:type" content="(.*?)">', content)
            self.assertIsNotNone(og_type, f"Missing og:type on {page_name}")
            self.assertEqual(og_type.group(1).strip(), "website")

            og_url = re.search(r'<meta property="og:url" content="(.*?)">', content)
            self.assertIsNotNone(og_url, f"Missing og:url on {page_name}")
            self.assertTrue(bool(og_url.group(1).strip()), f"Empty og:url on {page_name}")

            tw_card = re.search(r'<meta name="twitter:card" content="(.*?)">', content)
            self.assertIsNotNone(tw_card, f"Missing twitter:card on {page_name}")
            self.assertEqual(tw_card.group(1).strip(), "summary")

            tw_title = re.search(r'<meta name="twitter:title" content="(.*?)">', content)
            self.assertIsNotNone(tw_title, f"Missing twitter:title on {page_name}")
            self.assertTrue(bool(tw_title.group(1).strip()), f"Empty twitter:title on {page_name}")

            tw_desc = re.search(r'<meta name="twitter:description" content="(.*?)">', content)
            self.assertIsNotNone(tw_desc, f"Missing twitter:description on {page_name}")
            self.assertTrue(bool(tw_desc.group(1).strip()), f"Empty twitter:description on {page_name}")

            # Ensure no og:image yet
            self.assertNotIn('property="og:image"', content)

    def test_page_titles_and_descriptions_length(self):
        pages = ['core:home', 'core:services', 'core:gallery', 'core:about', 'core:contact']
        for page_name in pages:
            response = self.client.get(reverse(page_name))
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()

            title_match = re.search(r'<title>(.*?)</title>', content)
            self.assertIsNotNone(title_match, f"Missing title on {page_name}")
            title = title_match.group(1).strip()
            self.assertLessEqual(len(title), 60, f"Title too long on {page_name}: {title}")

            desc_match = re.search(r'<meta name="description" content="(.*?)">', content)
            self.assertIsNotNone(desc_match, f"Missing description on {page_name}")
            desc = desc_match.group(1).strip()
            self.assertLessEqual(len(desc), 160, f"Description too long on {page_name}: {desc}")

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
    def test_404_page_has_noindex_meta_tag(self):
        response = self.client.get('/this-path-does-not-exist-at-all-12345/')
        self.assertEqual(response.status_code, 404)
        content = response.content.decode()
        self.assertIn('<meta name="robots" content="noindex, nofollow">', content)
