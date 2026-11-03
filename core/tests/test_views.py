import re
from pathlib import Path
from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.urls import reverse
from core.models import Service


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
        # Verify AI labels are removed from route board
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

        # Form presence and CSRF
        self.assertIn('<form', content)
        self.assertIn('csrfmiddlewaretoken', content)

        # Honeypot field
        self.assertIn('name="website"', content)

        # Form input fields
        self.assertIn('name="name"', content)
        self.assertIn('name="phone"', content)
        self.assertIn('name="move_type"', content)
        self.assertIn('name="moving_from"', content)
        self.assertIn('name="moving_to"', content)
        self.assertIn('name="preferred_date"', content)
        self.assertIn('name="details"', content)

        # Submit button text
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
        """Verify compiled CSS defines both light and dark token sets and lorry orange / route green."""
        css_path = Path(settings.BASE_DIR) / 'static' / 'css' / 'output.css'
        self.assertTrue(css_path.exists(), f"Compiled CSS not found at {css_path}")
        css_content = css_path.read_text(encoding='utf-8')

        # Light tokens
        self.assertIn('--color-bg-page:#fff', css_content)
        self.assertIn('--color-bg-alt:#f4f6f8', css_content)
        self.assertIn('--color-text-heading:#16325c', css_content)
        self.assertIn('--color-text-body:#1f2933', css_content)
        self.assertIn('--color-text-muted:#52606d', css_content)
        self.assertIn('--color-border:#d9e0e6', css_content)

        # Dark tokens (deep navy)
        self.assertIn('--color-bg-page:#0f1b2d', css_content)
        self.assertIn('--color-bg-alt:#16263c', css_content)
        self.assertIn('--color-border:#2b3e57', css_content)
        self.assertIn('--color-bg-header:#0b1524', css_content)

        # Shared brand tokens
        self.assertIn('#f26b1d', css_content)  # lorry orange
        self.assertIn('#0b6b3a', css_content)  # route green

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

        # Check section container alignment
        self.assertIn('id="quote-form"', content)
        self.assertIn('max-w-6xl mx-auto px-4 sm:px-6 lg:px-8', content)

        # Check 2-column desktop grid
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
