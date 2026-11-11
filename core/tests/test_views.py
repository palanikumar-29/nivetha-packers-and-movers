import re
import tempfile
import shutil
from datetime import timedelta
from pathlib import Path
from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Service, GalleryImage, QuoteRequest


class HomePageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('core:home')

    def test_home_page_returns_http_200(self):
        """Verify GET / returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_page_has_exactly_one_h1(self):
        """Verify the Home page has exactly one <h1> element."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        self.assertEqual(len(h1_matches), 1, f"Expected exactly 1 <h1>, found {len(h1_matches)}: {h1_matches}")
        self.assertIn("Packers and movers in Tiruppur", h1_matches[0])

    def test_seo_title_and_description_presence_and_limits(self):
        """Verify title is <= 60 chars and meta description is <= 160 chars."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(title_match, "Title tag is missing")
        title = title_match.group(1).strip()
        self.assertTrue(len(title) > 0, "Title tag is empty")
        self.assertLessEqual(len(title), 60, f"Title exceeds 60 chars ({len(title)}): {title}")

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(desc_match, "Meta description tag is missing")
        description = desc_match.group(1).strip()
        self.assertTrue(len(description) > 0, "Meta description is empty")
        self.assertLessEqual(len(description), 160, f"Description exceeds 160 chars ({len(description)}): {description}")

    def test_color_scheme_meta_tag_present(self):
        """Verify color-scheme meta tag is present for native light/dark handling."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<meta name="color-scheme" content="light dark">', content)

    def test_canonical_link_present(self):
        """Verify canonical link is present in head."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<link rel="canonical"', content)

    def test_semantic_html_structure(self):
        """Verify header, nav, main, section, footer, and skip link are present."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<header', content)
        self.assertIn('<nav', content)
        self.assertIn('<main id="main-content"', content)
        self.assertIn('<section', content)
        self.assertIn('<footer', content)
        self.assertIn('href="#main-content"', content)

    def test_route_board_content_present_in_plain_html(self):
        """Verify highway route board contains Tiruppur, Chennai, Madurai, Nearby towns in plain HTML."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("Tiruppur", content)
        self.assertIn("Chennai", content)
        self.assertIn("Madurai", content)
        self.assertIn("Nearby towns", content)
        self.assertNotIn("ROUTE 47", content)
        self.assertNotIn("TAMIL NADU CORRIDOR", content)
        self.assertNotIn("ORIGIN HUB", content)
        self.assertNotIn("NORTH ROUTE", content)
        self.assertNotIn("SOUTH ROUTE", content)

    def test_services_summary_from_database(self):
        """Verify active services from DB render in order, inactive are excluded."""
        Service.objects.create(title='Commercial office moving', description='Desks and furniture shifted.', order=2, is_active=True)
        Service.objects.create(title='Household shifting', description='Safe home items shifting.', order=1, is_active=True)
        Service.objects.create(title='Secret Moving Service', description='Hidden service.', order=3, is_active=False)

        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("Household shifting", content)
        self.assertIn("Commercial office moving", content)
        self.assertNotIn("Secret Moving Service", content)

        pos_household = content.index("Household shifting")
        pos_office = content.index("Commercial office moving")
        self.assertLess(pos_household, pos_office)

    def test_services_empty_state_fallback(self):
        """Verify friendly fallback message when no active services exist in database."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("We will list our services here shortly", content)

    def test_quote_form_markup_fields_and_csrf_and_honeypot(self):
        """Verify quote form markup has CSRF token, honeypot, required inputs, and 'Send request' CTA."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        self.assertIn('<form', content)
        self.assertIn('csrfmiddlewaretoken', content)
        self.assertIn('name="website"', content)
        self.assertIn('name="name"', content)
        self.assertIn('name="phone"', content)
        self.assertIn('name="move_type"', content)
        self.assertIn('name="moving_from"', content)
        self.assertIn('name="moving_to"', content)
        self.assertIn('name="preferred_date"', content)
        self.assertIn('name="details"', content)
        self.assertIn("Send request", content)
        self.assertNotIn("Request free quote", content)

    def test_theme_toggle_button_present_with_aria_attributes(self):
        """Verify theme toggle button exists in header with accessible aria attributes and >= 44px target."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('id="theme-toggle"', content)
        self.assertIn('aria-label="Toggle theme"', content)
        self.assertIn('aria-pressed="false"', content)
        self.assertIn('w-11 h-11', content)

    def test_inline_theme_script_in_head(self):
        """Verify inline theme script is placed in <head> to prevent theme flash before paint."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        head_match = re.search(r'<head>(.*?)</head>', content, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(head_match, "Head section missing")
        head_content = head_match.group(1)
        self.assertIn("localStorage.getItem('theme')", head_content)
        self.assertIn("setAttribute('data-theme'", head_content)

    def test_both_theme_token_sets_present_in_compiled_css(self):
        """Verify compiled CSS defines both light and dark beige token sets and button tokens."""
        css_path = Path(settings.BASE_DIR) / 'static' / 'css' / 'output.css'
        self.assertTrue(css_path.exists(), f"Compiled CSS not found at {css_path}")
        css_content = css_path.read_text(encoding='utf-8').lower()

        self.assertIn('--color-bg-page:#ebe2cc', css_content)
        self.assertIn('--color-bg-alt:#ded6c1', css_content)
        self.assertIn('--color-text-heading:#16325c', css_content)
        self.assertIn('--color-text-body:#26221a', css_content)
        self.assertIn('--color-text-muted:#5a5242', css_content)
        self.assertIn('--color-border:#b7b09e', css_content)
        self.assertIn('--color-bg-page:#1f1c16', css_content)
        self.assertIn('--color-bg-alt:#2a261d', css_content)
        self.assertIn('--color-border:#4a4436', css_content)
        self.assertIn('--color-bg-header:#151310', css_content)
        self.assertIn('--btn-primary-bg:#b5470f', css_content)
        self.assertIn('--btn-primary-bg:#f26b1d', css_content)
        self.assertIn('#0b6b3a', css_content)

    def test_ai_patterns_and_invented_claims_removed(self):
        """Verify AI clichés, eyebrow badges, and unconfirmed claims are not in page copy."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        forbidden_phrases = [
            "regular",
            "reliable",
            "trusted",
            "fast",
            "experienced",
            "years",
            "coimbatore",
            "guaranteed",
            "no hidden charges",
            "no upfront fees",
            "clear pricing",
            "full load and part load",
            "all major destinations",
            "cautious",
            "STEP 01",
            "WHAT WE MOVE",
            "TRANSIT STEPS",
            "NPM",
            "Get a Free Quote",
            "Request Free Quote",
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase.lower(), content.lower(), f"Forbidden phrase '{phrase}' was found in page content")

    def test_quote_section_aligned_container_and_two_column_desktop_layout(self):
        """Verify quote section has matching container width and 2-col desktop / 1-col mobile layout."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        self.assertIn('id="quote-form"', content)
        self.assertIn('max-w-6xl mx-auto px-4 sm:px-6 lg:px-8', content)
        self.assertIn('grid grid-cols-1 lg:grid-cols-12', content)
        self.assertIn('lg:col-span-5', content)
        self.assertIn('lg:col-span-7', content)

    @override_settings(BUSINESS_PHONE='919876543210', BUSINESS_WHATSAPP='919876543210')
    def test_contact_buttons_use_environment_settings(self):
        """Verify floating contact buttons and header CTA render links using env vars."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('tel:919876543210', content)
        self.assertIn('https://wa.me/919876543210', content)

    @override_settings(BUSINESS_PHONE='', BUSINESS_WHATSAPP='')
    def test_contact_buttons_when_empty_env(self):
        """Verify that when phone numbers are empty, template does not crash and does not hardcode numbers."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertNotIn('tel:9', content)
        self.assertNotIn('https://wa.me/9', content)


class ServicesPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('core:services')

    def test_services_page_returns_http_200(self):
        """Verify GET /services/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_services_page_has_exactly_one_h1(self):
        """Verify Services page has exactly one <h1> element."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        self.assertEqual(len(h1_matches), 1, f"Expected 1 <h1>, found {len(h1_matches)}")
        self.assertIn("Moving services in Tiruppur", h1_matches[0])

    def test_seo_title_and_description_limits(self):
        """Verify title is <= 60 chars and meta description is <= 160 chars."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(title_match)
        title = title_match.group(1).strip()
        self.assertLessEqual(len(title), 60)

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(desc_match)
        description = desc_match.group(1).strip()
        self.assertLessEqual(len(description), 160)

    def test_canonical_link_present(self):
        """Verify canonical link is present matching /services/."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<link rel="canonical"', content)
        self.assertIn('/services/', content)

    def test_local_keywords_present(self):
        """Verify Tiruppur, Chennai, and Madurai appear naturally in copy."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("Tiruppur", content)
        self.assertIn("Chennai", content)
        self.assertIn("Madurai", content)

    def test_services_active_ordering_and_inactive_excluded(self):
        """Verify active services display in order and inactive services are excluded."""
        Service.objects.create(title='Vehicle Moving', description='Two-wheelers transported.', order=2, is_active=True)
        Service.objects.create(title='House Moving', description='Household items shifted.', order=1, is_active=True)
        Service.objects.create(title='Inactive Service', description='Hidden.', order=0, is_active=False)

        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("House Moving", content)
        self.assertIn("Vehicle Moving", content)
        self.assertNotIn("Inactive Service", content)

        pos1 = content.index("House Moving")
        pos2 = content.index("Vehicle Moving")
        self.assertLess(pos1, pos2)

    def test_services_empty_state(self):
        """Verify friendly fallback message when no services are in database."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("We will list our services here shortly", content)

    def test_quote_cta_links_to_contact_page_form(self):
        """Verify CTA at end links to contact quote form."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn(reverse('core:contact') + '#quote-form', content)


class GalleryPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('core:gallery')
        self.temp_media = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_gallery_page_returns_http_200(self):
        """Verify GET /gallery/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_gallery_page_has_exactly_one_h1(self):
        """Verify Gallery page has exactly one <h1> element."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        self.assertEqual(len(h1_matches), 1, f"Expected 1 <h1>, found {len(h1_matches)}")
        self.assertIn("Our work in photos", h1_matches[0])

    def test_seo_title_and_description_limits(self):
        """Verify title is <= 60 chars and meta description is <= 160 chars."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(title_match)
        self.assertLessEqual(len(title_match.group(1).strip()), 60)

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(desc_match)
        self.assertLessEqual(len(desc_match.group(1).strip()), 160)

    def test_canonical_link_present(self):
        """Verify canonical link is present matching /gallery/."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<link rel="canonical"', content)
        self.assertIn('/gallery/', content)

    def test_gallery_images_display_lazy_loading_and_alt_text(self):
        """Verify active GalleryImage renders with loading=lazy, width, height, and caption as alt."""
        with override_settings(MEDIA_ROOT=self.temp_media):
            dummy_file = SimpleUploadedFile('truck.gif', b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b', content_type='image/gif')
            GalleryImage.objects.create(image=dummy_file, caption='Packing household goods in Tiruppur', order=1, is_active=True)

            inactive_file = SimpleUploadedFile('secret.gif', b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b', content_type='image/gif')
            GalleryImage.objects.create(image=inactive_file, caption='Hidden photo', order=2, is_active=False)

            response = self.client.get(self.url)
            content = response.content.decode('utf-8')
            self.assertIn('loading="lazy"', content)
            self.assertIn('width="600"', content)
            self.assertIn('height="450"', content)
            self.assertIn('alt="Packing household goods in Tiruppur"', content)
            self.assertIn('Packing household goods in Tiruppur', content)
            self.assertNotIn('Hidden photo', content)

    def test_gallery_empty_state(self):
        """Verify friendly fallback message when no gallery images are in database."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("We will post photos of our moves here shortly", content)

    def test_local_media_pattern_configured_when_debug(self):
        """Verify media URL pattern matches uploaded files when DEBUG=True."""
        with override_settings(DEBUG=True):
            from django.conf.urls.static import static
            patterns = static(settings.MEDIA_URL, document_root=self.temp_media)
            self.assertEqual(len(patterns), 1)
            self.assertIsNotNone(patterns[0].pattern.match('media/gallery/sample.jpg'))


class AboutPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('core:about')

    def test_about_page_returns_http_200(self):
        """Verify GET /about/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_about_page_has_exactly_one_h1(self):
        """Verify About page has exactly one <h1> element."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        self.assertEqual(len(h1_matches), 1, f"Expected 1 <h1>, found {len(h1_matches)}")
        self.assertIn("About Nivetha Packers and Movers", h1_matches[0])

    def test_seo_title_and_description_limits(self):
        """Verify title is <= 60 chars and meta description is <= 160 chars."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(title_match)
        self.assertLessEqual(len(title_match.group(1).strip()), 60)

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(desc_match)
        self.assertLessEqual(len(desc_match.group(1).strip()), 160)

    def test_canonical_link_present(self):
        """Verify canonical link is present matching /about/."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<link rel="canonical"', content)
        self.assertIn('/about/', content)

    def test_neutral_copy_only_without_invented_claims(self):
        """Verify About page only says what is known without fabricated claims."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("Tiruppur", content)
        self.assertIn("Chennai", content)
        self.assertIn("Madurai", content)
        self.assertIn("Household shifting", content)
        self.assertIn("Office relocation", content)
        self.assertIn("Vehicle transport", content)


class ContactPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('core:contact')

    def test_contact_page_returns_http_200(self):
        """Verify GET /contact/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contact_page_has_exactly_one_h1(self):
        """Verify Contact page has exactly one <h1> element."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        self.assertEqual(len(h1_matches), 1, f"Expected 1 <h1>, found {len(h1_matches)}")
        self.assertIn("Contact Nivetha Packers and Movers", h1_matches[0])

    def test_seo_title_and_description_limits(self):
        """Verify title is <= 60 chars and meta description is <= 160 chars."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(title_match)
        self.assertLessEqual(len(title_match.group(1).strip()), 60)

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(desc_match)
        self.assertLessEqual(len(desc_match.group(1).strip()), 160)

    def test_canonical_link_present(self):
        """Verify canonical link is present matching /contact/."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<link rel="canonical"', content)
        self.assertIn('/contact/', content)

    @override_settings(BUSINESS_PHONE='919876543210', BUSINESS_WHATSAPP='919876543210', BUSINESS_ADDRESS='123 Avinashi Road, Tiruppur, Tamil Nadu')
    def test_contact_details_render_from_settings(self):
        """Verify phone, WhatsApp, and address are rendered from settings/env."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('tel:919876543210', content)
        self.assertIn('https://wa.me/919876543210', content)
        self.assertIn('123 Avinashi Road, Tiruppur, Tamil Nadu', content)

    def test_quote_form_markup_present_in_contact_page(self):
        """Verify quote form partial is included in Contact page with CSRF and honeypot."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('id="quote-form"', content)
        self.assertIn('csrfmiddlewaretoken', content)
        self.assertIn('name="website"', content)
        self.assertIn('name="name"', content)
        self.assertIn('name="phone"', content)
        self.assertIn('Send request', content)


class CrossPageSiteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.urls = {
            'home': reverse('core:home'),
            'services': reverse('core:services'),
            'gallery': reverse('core:gallery'),
            'about': reverse('core:about'),
            'contact': reverse('core:contact'),
        }

    def test_all_five_pages_return_http_200(self):
        """Verify each of the 5 public pages returns HTTP 200."""
        for name, url in self.urls.items():
            with self.subTest(page=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_each_page_has_unique_title_and_description(self):
        """Verify title and meta description are unique across all 5 pages."""
        titles = set()
        descriptions = set()

        for name, url in self.urls.items():
            response = self.client.get(url)
            content = response.content.decode('utf-8')

            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            self.assertIsNotNone(title_match, f"Missing title in {name}")
            title = title_match.group(1).strip()
            self.assertNotIn(title, titles, f"Duplicate title found on {name}: {title}")
            titles.add(title)

            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
            self.assertIsNotNone(desc_match, f"Missing meta description in {name}")
            desc = desc_match.group(1).strip()
            self.assertNotIn(desc, descriptions, f"Duplicate description found on {name}: {desc}")
            descriptions.add(desc)

        self.assertEqual(len(titles), 5)
        self.assertEqual(len(descriptions), 5)

    def test_navigation_links_to_all_five_pages_in_header_and_footer(self):
        """Verify header and footer contain links to all 5 pages from any page."""
        response = self.client.get(self.urls['home'])
        content = response.content.decode('utf-8')

        for name, url in self.urls.items():
            with self.subTest(target=name):
                self.assertIn(f'href="{url}"', content)

    def test_mobile_menu_details_present_with_accessible_targets(self):
        """Verify zero-JS <details> mobile menu exists with min-h-[44px] tap targets."""
        response = self.client.get(self.urls['home'])
        content = response.content.decode('utf-8')
        self.assertIn('<details class="md:hidden', content)
        self.assertIn('aria-label="Toggle navigation menu"', content)
        self.assertIn('min-h-[44px]', content)

    def test_quote_form_partial_used_on_both_home_and_contact(self):
        """Verify quote form is present on both Home and Contact pages with identical inputs."""
        home_content = self.client.get(self.urls['home']).content.decode('utf-8')
        contact_content = self.client.get(self.urls['contact']).content.decode('utf-8')

        for content, page_name in [(home_content, 'Home'), (contact_content, 'Contact')]:
            self.assertIn('name="website"', content, f"Honeypot missing on {page_name}")
            self.assertIn('name="name"', content, f"Name input missing on {page_name}")
            self.assertIn('name="phone"', content, f"Phone input missing on {page_name}")
            self.assertIn('name="move_type"', content, f"Move type select missing on {page_name}")
            self.assertIn('name="moving_from"', content, f"Moving from missing on {page_name}")
            self.assertIn('name="moving_to"', content, f"Moving to missing on {page_name}")
            self.assertIn('Send request', content, f"Submit CTA missing on {page_name}")

    def test_forbidden_words_absent_across_all_five_pages(self):
        """Verify unconfirmed claims are not present on any of the 5 pages."""
        forbidden_phrases = [
            "regular",
            "reliable",
            "trusted",
            "fast",
            "experienced",
            "years",
            "coimbatore",
            "guaranteed",
        ]
        for name, url in self.urls.items():
            response = self.client.get(url)
            content = response.content.decode('utf-8').lower()
            for phrase in forbidden_phrases:
                with self.subTest(page=name, phrase=phrase):
                    self.assertNotIn(phrase, content, f"Forbidden phrase '{phrase}' found on page {name}")


class QuoteFormSubmissionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact_url = reverse('core:contact')
        self.home_url = reverse('core:home')
        self.future_date = (timezone.localdate() + timedelta(days=5)).isoformat()
        self.valid_payload = {
            'name': 'Ramesh Kumar',
            'phone': '9876543210',
            'move_type': 'house',
            'moving_from': 'Tiruppur',
            'moving_to': 'Chennai',
            'preferred_date': self.future_date,
            'details': 'Household shifting 2 BHK',
            'website': '',
        }

    def test_valid_submission_on_contact_creates_enquiry_and_redirects(self):
        """Verify valid submission on /contact/ creates QuoteRequest with status=New and redirects."""
        response = self.client.post(self.contact_url, data=self.valid_payload)
        self.assertEqual(response.status_code, 302)
        self.assertIn('?submitted=1#quote-form', response.url)

        self.assertEqual(QuoteRequest.objects.count(), 1)
        enquiry = QuoteRequest.objects.first()
        self.assertEqual(enquiry.name, 'Ramesh Kumar')
        self.assertEqual(enquiry.phone, '9876543210')
        self.assertEqual(enquiry.status, 'New')

        follow_res = self.client.get(response.url)
        self.assertEqual(follow_res.status_code, 200)
        self.assertIn("Thank you! Your quote request has been sent.", follow_res.content.decode('utf-8'))

    def test_valid_submission_on_home_creates_enquiry_and_redirects(self):
        """Verify valid submission on / creates QuoteRequest with status=New and redirects."""
        response = self.client.post(self.home_url, data=self.valid_payload)
        self.assertEqual(response.status_code, 302)
        self.assertIn('?submitted=1#quote-form', response.url)

        self.assertEqual(QuoteRequest.objects.count(), 1)
        enquiry = QuoteRequest.objects.first()
        self.assertEqual(enquiry.name, 'Ramesh Kumar')
        self.assertEqual(enquiry.status, 'New')

        follow_res = self.client.get(response.url)
        self.assertEqual(follow_res.status_code, 200)
        self.assertIn("Thank you! Your quote request has been sent.", follow_res.content.decode('utf-8'))

    def test_invalid_phone_rerenders_form_with_inline_error_and_zero_enquiries(self):
        """Verify bad phone (8 digits) re-renders form with inline error and creates zero enquiries."""
        bad_payload = dict(self.valid_payload)
        bad_payload['phone'] = '98765432'  # Only 8 digits

        response = self.client.post(self.contact_url, data=bad_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 0)

        content = response.content.decode('utf-8')
        self.assertIn("Phone number must be a 10-digit Indian mobile number", content)
        self.assertIn('value="Ramesh Kumar"', content)

    def test_past_preferred_date_rerenders_form_with_inline_error_and_zero_enquiries(self):
        """Verify past move date re-renders form with inline error and creates zero enquiries."""
        past_date = (timezone.localdate() - timedelta(days=2)).isoformat()
        bad_payload = dict(self.valid_payload)
        bad_payload['preferred_date'] = past_date

        response = self.client.post(self.contact_url, data=bad_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 0)

        content = response.content.decode('utf-8')
        self.assertIn("Preferred move date must be today or a future date.", content)

    def test_missing_required_fields_rerenders_form_with_inline_errors_and_zero_enquiries(self):
        """Verify missing required fields re-render form with inline errors and create zero enquiries."""
        incomplete_payload = {
            'name': 'Priya',
            'phone': '',
            'move_type': '',
            'moving_from': '',
            'moving_to': '',
        }
        response = self.client.post(self.contact_url, data=incomplete_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 0)

        content = response.content.decode('utf-8')
        self.assertIn("This field is required.", content)

    def test_honeypot_bot_submission_returns_fake_success_with_zero_enquiries(self):
        """Verify bot submission with non-empty honeypot returns fake success and creates zero enquiries."""
        spam_payload = dict(self.valid_payload)
        spam_payload['website'] = 'https://automated-spam-attack.com'

        response = self.client.post(self.contact_url, data=spam_payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(QuoteRequest.objects.count(), 0)

        follow_res = self.client.get(response.url)
        self.assertEqual(follow_res.status_code, 200)
        self.assertIn("Thank you! Your quote request has been sent.", follow_res.content.decode('utf-8'))

    def test_csrf_protection_enforced_on_quote_form_post(self):
        """Verify POST without CSRF token returns HTTP 403 Forbidden when CSRF checks are enforced."""
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(self.contact_url, data=self.valid_payload)
        self.assertEqual(response.status_code, 403)


