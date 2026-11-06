import re
from django.test import TestCase
from django.urls import reverse


class IntroAnimationTest(TestCase):
    """
    Story 1.7: Opening Animation (Home page intro) tests covering:
    - Non-JS hero accessibility and presence of single H1 and quote CTA
    - Presence of intro overlay only on Home (never on other pages or 404)
    - Skip button accessibility, label, and min-touch target
    - Size budget: inline script and CSS stay within 4 KB (4096 bytes)
    - Presence of reduced-motion, save-data, and low-end device detection
    - Absence of external animation frameworks, videos, or libraries
    """

    def test_home_html_contains_single_h1_and_quote_cta_without_js(self):
        """Home page rendered without JS contains exactly one H1 and quote CTA."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Single H1 heading
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
        self.assertEqual(len(h1_matches), 1, "Expected exactly one <h1> on Home page")
        self.assertIn("Packers and movers in Tiruppur", h1_matches[0])

        # Quote Call to Action exists
        self.assertTrue(
            ('href="#quote-form"' in content or 'Get a quote' in content) and
            ('Request a quote' in content),
            "Quote CTA not found in Home HTML"
        )

    def test_overlay_markup_appears_exactly_once_and_only_on_home(self):
        """Intro overlay markup appears exactly once on Home, and is absent on all other pages and 404."""
        # 1. Home page contains overlay exactly once
        home_resp = self.client.get(reverse('core:home'))
        self.assertEqual(home_resp.status_code, 200)
        home_content = home_resp.content.decode('utf-8')
        overlay_occurrences = home_content.count('id="intro-overlay"')
        self.assertEqual(overlay_occurrences, 1, "Intro overlay should appear exactly once on Home")
        self.assertIn('aria-hidden="true"', home_content)

        # 2. Public other pages do not contain intro overlay
        other_pages = ['core:services', 'core:gallery', 'core:about', 'core:contact']
        for page_name in other_pages:
            resp = self.client.get(reverse(page_name))
            self.assertEqual(resp.status_code, 200)
            page_content = resp.content.decode('utf-8')
            self.assertNotIn('id="intro-overlay"', page_content, f"Intro overlay should not exist on {page_name}")
            self.assertNotIn('intro-skip', page_content, f"Intro skip button should not exist on {page_name}")

        # 3. 404 page does not contain intro overlay
        resp_404 = self.client.get('/this-path-does-not-exist-12345/')
        self.assertEqual(resp_404.status_code, 404)
        page_404_content = resp_404.content.decode('utf-8')
        self.assertNotIn('id="intro-overlay"', page_404_content)

    def test_skip_button_exists_with_accessible_label_and_touch_target(self):
        """Skip button exists, has text 'Skip', an accessible aria-label, and min 44px dimensions."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        match = re.search(r'<button[^>]*id="intro-skip"[^>]*>(.*?)</button>', content, re.DOTALL)
        self.assertIsNotNone(match, "Skip button id='intro-skip' not found")
        btn_tag = match.group(0)
        btn_text = match.group(1).strip()

        # Text label is exactly "Skip"
        self.assertEqual(btn_text, "Skip")

        # Accessible label
        self.assertIn('aria-label="Skip intro animation"', btn_tag)

        # Touch target styling
        self.assertIn('min-height:44px', content.replace(' ', ''))
        self.assertIn('min-width:44px', content.replace(' ', ''))

    def test_inline_script_and_css_size_budget_under_4kb(self):
        """The inline intro script and CSS must stay within the 4 KB (4096 bytes) budget."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Extract head script and styles for intro
        head_match = re.search(r'{% block extra_head %}(.*?){% endblock %}', content, re.DOTALL)
        # In rendered HTML, extra_head is placed inside <head>
        scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
        styles = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)

        # Identify intro script and intro styles
        intro_scripts = [s for s in scripts if 'intro-play' in s or 'intro-skip' in s or 'intro_seen' in s]
        intro_styles = [s for s in styles if 'intro-overlay' in s]

        self.assertTrue(len(intro_scripts) >= 1, "Intro script not found")
        self.assertTrue(len(intro_styles) >= 1, "Intro style not found")

        total_script_bytes = sum(len(s.encode('utf-8')) for s in intro_scripts)
        total_style_bytes = sum(len(s.encode('utf-8')) for s in intro_styles)
        total_weight = total_script_bytes + total_style_bytes

        self.assertLessEqual(
            total_weight,
            4096,
            f"Intro inline script ({total_script_bytes}B) and CSS ({total_style_bytes}B) total {total_weight}B exceeds 4096B (4 KB) budget"
        )

    def test_intro_script_checks_reduced_motion_save_data_and_low_end(self):
        """Script includes checks for prefers-reduced-motion, saveData, sessionStorage, and low-end devices."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('prefers-reduced-motion', content)
        self.assertIn('saveData', content)
        self.assertIn('sessionStorage', content)
        self.assertIn('intro_seen', content)
        self.assertIn('deviceMemory', content)
        self.assertIn('hardwareConcurrency', content)

    def test_no_external_animation_libraries_or_assets(self):
        """Verifies no external animation libraries (Lottie, GSAP), video files, or GIFs are added."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8').lower()

        forbidden_tokens = ['lottie', 'gsap', 'anime.js', 'three.js', '.mp4', '.webm', '.gif']
        for token in forbidden_tokens:
            self.assertNotIn(token, content, f"Forbidden animation asset or library found: {token}")
