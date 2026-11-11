import re
from pathlib import Path
from django.test import TestCase, override_settings
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.conf import settings
from django.contrib import admin
from core.models import SiteSettings, PALETTES, PALETTE_NAMES, DEFAULT_PALETTE


def relative_luminance(hex_color: str) -> float:
    hex_clean = hex_color.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join(c * 2 for c in hex_clean)
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0
    channels = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        for c in (r, g, b)
    ]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(color1: str, color2: str) -> float:
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class PalettePresetsTest(TestCase):
    """
    Story 2.4: Palette Presets tests covering singleton model, switching on all pages,
    unknown fallback, admin permissions, and WCAG AA contrast for every preset.
    """

    def setUp(self):
        cache.clear()
        SiteSettings.objects.all().delete()
        self.superuser = User.objects.create_superuser(
            username='admin_palette',
            password='Password123!',
            email='admin@example.com'
        )
        self.client_group, _ = Group.objects.get_or_create(name='Client')
        self.client_user = User.objects.create_user(
            username='client_palette',
            password='Password123!',
            is_staff=True
        )
        self.client_user.groups.add(self.client_group)

    def tearDown(self):
        cache.clear()

    def test_default_palette_is_beige(self):
        """Default palette is 'beige' when no row exists and SITE_PALETTE is unset."""
        self.assertEqual(SiteSettings.get_solo(), 'beige')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-palette="beige"', response.content.decode('utf-8'))

    @override_settings(SITE_PALETTE='navy')
    def test_default_palette_respects_env_setting(self):
        """When SITE_PALETTE setting is provided, default matches it."""
        cache.clear()
        self.assertEqual(SiteSettings.get_solo(), 'navy')
        response = self.client.get('/')
        self.assertIn('data-palette="navy"', response.content.decode('utf-8'))

    def test_switching_palette_changes_data_palette_on_all_five_pages(self):
        """Switching via SiteSettings updates data-palette on all five public pages immediately."""
        settings_obj = SiteSettings.objects.create(palette='navy')
        settings_obj.save()

        pages = ['/', '/services/', '/gallery/', '/about/', '/contact/']
        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Page {url} returned non-200")
            content = response.content.decode('utf-8')
            self.assertIn('data-palette="navy"', content, f"Page {url} missing data-palette='navy'")

        # Switch back to beige
        settings_obj.palette = 'beige'
        settings_obj.save()

        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            content = response.content.decode('utf-8')
            self.assertIn('data-palette="beige"', content, f"Page {url} missing data-palette='beige'")

    def test_unknown_palette_falls_back_to_default(self):
        """Invalid or unknown palette string in DB falls back safely to default."""
        cache.clear()
        # Direct DB write of invalid palette bypassing form choices
        SiteSettings.objects.filter(pk=1).delete()
        obj = SiteSettings(palette='neon_magenta')
        obj.pk = 1
        super(SiteSettings, obj).save()
        cache.clear()

        # Should fall back to DEFAULT_PALETTE
        self.assertEqual(SiteSettings.get_solo(), DEFAULT_PALETTE)
        response = self.client.get('/')
        self.assertIn(f'data-palette="{DEFAULT_PALETTE}"', response.content.decode('utf-8'))

    def test_sitesettings_singleton_enforcement(self):
        """Only one SiteSettings row can exist and delete is prevented."""
        s1 = SiteSettings.objects.create(palette='beige')
        self.assertEqual(s1.pk, 1)

        # Attempt creating another instance
        s2 = SiteSettings(palette='navy')
        s2.save()
        self.assertEqual(s2.pk, 1)
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.objects.get(pk=1).palette, 'navy')

        # Attempt deleting
        s2.delete()
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_superuser_can_change_sitesettings_in_admin(self):
        """Superuser can access and update Site settings in /panel/."""
        SiteSettings.objects.create(palette='beige')
        self.client.login(username='admin_palette', password='Password123!')

        resp_get = self.client.get('/panel/core/sitesettings/1/change/')
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn('palette', resp_get.content.decode('utf-8'))

        resp_post = self.client.post('/panel/core/sitesettings/1/change/', {'palette': 'navy'})
        self.assertEqual(resp_post.status_code, 302)
        self.assertEqual(SiteSettings.objects.get(pk=1).palette, 'navy')
        self.assertEqual(SiteSettings.get_solo(), 'navy')

    def test_client_user_cannot_access_sitesettings_in_admin(self):
        """Client group users cannot access or view Site settings."""
        SiteSettings.objects.create(palette='beige')
        self.client.login(username='client_palette', password='Password123!')

        resp = self.client.get('/panel/core/sitesettings/')
        self.assertEqual(resp.status_code, 403)

        resp_change = self.client.get('/panel/core/sitesettings/1/change/')
        self.assertEqual(resp_change.status_code, 403)

    def test_admin_prevents_adding_second_row_and_deletion(self):
        """SiteSettingsAdmin disallows add once a row exists and completely disallows delete."""
        site_admin = admin.site._registry[SiteSettings]
        from django.test import RequestFactory
        factory = RequestFactory()
        req = factory.get('/panel/core/sitesettings/')
        req.user = self.superuser

        # No row exists yet
        SiteSettings.objects.all().delete()
        self.assertTrue(site_admin.has_add_permission(req))

        # Once a row exists, add is prohibited
        SiteSettings.objects.create(palette='beige')
        self.assertFalse(site_admin.has_add_permission(req))
        self.assertFalse(site_admin.has_delete_permission(req))

    def test_contrast_ratios_per_preset_meet_wcag_aa(self):
        """
        Verify WCAG AA contrast (>= 4.5:1 text, >= 3:1 UI borders/focus) for every preset
        in both light and dark themes.
        """
        presets = {
            'beige': {
                'light': {
                    'page': '#EBE2CC',
                    'heading': '#16325C',
                    'body': '#26221A',
                    'muted': '#5A5242',
                    'btn_primary_bg': '#B5470F',
                    'btn_primary_text': '#FFFFFF',
                    'btn_secondary_text': '#16325C',
                    'btn_secondary_outline': '#16325C',
                    'focus_ring': '#16325C',
                    'footer_bg': '#26221A',
                    'footer_text': '#EBE2CC',
                },
                'dark': {
                    'page': '#1F1C16',
                    'heading': '#EBE2CC',
                    'body': '#EBE2CC',
                    'muted': '#B7B09E',
                    'btn_primary_bg': '#F26B1D',
                    'btn_primary_text': '#1F1C16',
                    'btn_secondary_text': '#EBE2CC',
                    'btn_secondary_outline': '#EBE2CC',
                    'focus_ring': '#EBE2CC',
                    'footer_bg': '#151310',
                    'footer_text': '#EBE2CC',
                },
            },
            'navy': {
                'light': {
                    'page': '#FFFFFF',
                    'heading': '#16325C',
                    'body': '#1F2933',
                    'muted': '#52606D',
                    'btn_primary_bg': '#F26B1D',
                    'btn_primary_text': '#1F2933',
                    'btn_secondary_text': '#16325C',
                    'btn_secondary_outline': '#16325C',
                    'focus_ring': '#16325C',
                    'footer_bg': '#16325C',
                    'footer_text': '#F3F5F2',
                },
                'dark': {
                    'page': '#0F1B2D',
                    'heading': '#FFFFFF',
                    'body': '#E8EDF3',
                    'muted': '#A9B6C6',
                    'btn_primary_bg': '#F26B1D',
                    'btn_primary_text': '#0F1B2D',
                    'btn_secondary_text': '#FFFFFF',
                    'btn_secondary_outline': '#FFFFFF',
                    'focus_ring': '#FFFFFF',
                    'footer_bg': '#0B1524',
                    'footer_text': '#E8EDF3',
                },
            },
        }

        for preset_name, variants in presets.items():
            for variant_name, tokens in variants.items():
                label = f"{preset_name} ({variant_name})"

                # Text contrast (>= 4.5:1)
                r_body = contrast_ratio(tokens['body'], tokens['page'])
                self.assertGreaterEqual(r_body, 4.5, f"{label} body contrast failed: {r_body:.2f}:1")

                r_heading = contrast_ratio(tokens['heading'], tokens['page'])
                self.assertGreaterEqual(r_heading, 4.5, f"{label} heading contrast failed: {r_heading:.2f}:1")

                r_muted = contrast_ratio(tokens['muted'], tokens['page'])
                self.assertGreaterEqual(r_muted, 4.5, f"{label} muted contrast failed: {r_muted:.2f}:1")

                r_btn_primary = contrast_ratio(tokens['btn_primary_text'], tokens['btn_primary_bg'])
                self.assertGreaterEqual(r_btn_primary, 4.5, f"{label} btn primary contrast failed: {r_btn_primary:.2f}:1")

                r_btn_sec = contrast_ratio(tokens['btn_secondary_text'], tokens['page'])
                self.assertGreaterEqual(r_btn_sec, 4.5, f"{label} btn secondary text contrast failed: {r_btn_sec:.2f}:1")

                r_footer = contrast_ratio(tokens['footer_text'], tokens['footer_bg'])
                self.assertGreaterEqual(r_footer, 4.5, f"{label} footer text contrast failed: {r_footer:.2f}:1")

                # UI borders and focus rings (>= 3.0:1)
                r_focus = contrast_ratio(tokens['focus_ring'], tokens['page'])
                self.assertGreaterEqual(r_focus, 3.0, f"{label} focus ring contrast failed: {r_focus:.2f}:1")

                r_outline = contrast_ratio(tokens['btn_secondary_outline'], tokens['page'])
                self.assertGreaterEqual(r_outline, 3.0, f"{label} secondary outline contrast failed: {r_outline:.2f}:1")

    def test_no_hardcoded_hex_values_outside_token_definitions(self):
        """Verify no hardcoded hex values exist in any public HTML template."""
        templates_dir = Path(settings.BASE_DIR) / 'core' / 'templates'
        html_files = list(templates_dir.rglob('*.html'))
        self.assertGreater(len(html_files), 0, "No template files found")

        hex_pattern = re.compile(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}')
        for html_file in html_files:
            content = html_file.read_text(encoding='utf-8')
            matches = hex_pattern.findall(content)
            self.assertEqual(
                matches,
                [],
                f"Hardcoded hex colors found in {html_file.name}: {matches}"
            )
