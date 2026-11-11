from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.utils import timezone
from core.models import QuoteRequest, MoveType, EnquiryStatus, Service, GalleryImage


class ClientPanelTest(TestCase):
    """
    Story 2.1: Client Panel tests covering admin permissions, enquiry management,
    amber badge highlighting, wa.me customer link, and status updates.
    """

    def setUp(self):
        call_command('create_client_group')
        self.client_group = Group.objects.get(name='Client')

        self.client_user = User.objects.create_user(
            username='client_owner',
            password='Password123!',
            is_staff=True,
        )
        self.client_user.groups.add(self.client_group)

        self.superuser = User.objects.create_superuser(
            username='super_admin',
            password='Password123!',
            email='admin@example.com',
        )

    def test_default_admin_url_is_404(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 404)

    def test_create_client_group_creates_exact_ten_permissions(self):
        call_command('create_client_group')
        group = Group.objects.get(name='Client')
        perms = group.permissions.all()
        self.assertEqual(perms.count(), 10)

        codenames = set(perms.values_list('codename', flat=True))
        expected_codenames = {
            'view_quoterequest',
            'change_quoterequest',
            'view_service',
            'add_service',
            'change_service',
            'delete_service',
            'view_galleryimage',
            'add_galleryimage',
            'change_galleryimage',
            'delete_galleryimage',
        }
        self.assertEqual(codenames, expected_codenames)

        # Confirm no auth or session permissions
        app_labels = set(perms.values_list('content_type__app_label', flat=True))
        self.assertEqual(app_labels, {'core'})

    def test_client_user_panel_index_shows_enquiries_services_gallery_not_users(self):
        self.client.login(username='client_owner', password='Password123!')
        response = self.client.get('/panel/')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        self.assertIn('Enquiries', content)
        self.assertIn('Services', content)
        self.assertIn('Gallery', content)
        self.assertNotIn('Users', content)
        self.assertNotIn('Groups', content)
        self.assertNotIn('Site settings', content)

    def test_client_user_cannot_access_sitesettings(self):
        self.client.login(username='client_owner', password='Password123!')
        resp = self.client.get('/panel/core/sitesettings/')
        self.assertEqual(resp.status_code, 403)

    def test_superuser_can_access_sitesettings(self):
        self.client.login(username='super_admin', password='Password123!')
        resp = self.client.get('/panel/core/sitesettings/')
        self.assertEqual(resp.status_code, 200)

    def test_client_group_has_no_sitesettings_permissions(self):
        call_command('create_client_group')
        group = Group.objects.get(name='Client')
        self.assertFalse(group.permissions.filter(codename__endswith='sitesettings').exists())

    def test_client_user_cannot_access_auth_user_or_group(self):
        self.client.login(username='client_owner', password='Password123!')

        resp_user = self.client.get('/panel/auth/user/')
        self.assertIn(resp_user.status_code, [403, 302])

        resp_group = self.client.get('/panel/auth/group/')
        self.assertIn(resp_group.status_code, [403, 302])

    def test_superuser_can_access_auth_user(self):
        self.client.login(username='super_admin', password='Password123!')
        response = self.client.get('/panel/auth/user/')
        self.assertEqual(response.status_code, 200)

    def test_enquiry_list_with_new_status_contains_amber_highlight(self):
        QuoteRequest.objects.create(
            name='Test Customer',
            phone='9876543210',
            move_type=MoveType.HOUSE,
            moving_from='Tiruppur',
            moving_to='Chennai',
            status=EnquiryStatus.NEW,
        )

        self.client.login(username='client_owner', password='Password123!')
        response = self.client.get('/panel/core/quoterequest/')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        # Verify visual distinction via amber badge / highlight element
        self.assertTrue('amber-highlight' in content or 'badge-new' in content)
        self.assertIn('New', content)

    def test_enquiry_detail_renders_wame_anchor_tag_with_phone_and_summary(self):
        enquiry = QuoteRequest.objects.create(
            name='Ravi Kumar',
            phone='9876543210',
            move_type=MoveType.HOUSE,
            moving_from='Tiruppur',
            moving_to='Madurai',
            status=EnquiryStatus.NEW,
        )

        self.client.login(username='client_owner', password='Password123!')
        response = self.client.get(f'/panel/core/quoterequest/{enquiry.id}/change/')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        self.assertIn('wa.me/9876543210', content)
        self.assertIn('WhatsApp customer', content)
        self.assertIn('<a href="https://wa.me/9876543210', content)
        self.assertIn('Ravi%20Kumar', content)
        self.assertIn('Madurai', content)

    def test_status_change_from_new_to_called_persists_status_updated_at(self):
        enquiry = QuoteRequest.objects.create(
            name='Kavitha',
            phone='9876543210',
            move_type=MoveType.OFFICE,
            moving_from='Tiruppur',
            moving_to='Chennai',
            status=EnquiryStatus.NEW,
        )
        self.assertIsNone(enquiry.status_updated_at)

        self.client.login(username='client_owner', password='Password123!')
        post_data = {
            'status': EnquiryStatus.CALLED,
            'notes': 'Called customer and scheduled preliminary survey.',
        }
        response = self.client.post(
            f'/panel/core/quoterequest/{enquiry.id}/change/',
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        enquiry.refresh_from_db()
        self.assertEqual(enquiry.status, EnquiryStatus.CALLED)
        self.assertEqual(enquiry.notes, 'Called customer and scheduled preliminary survey.')
        self.assertIsNotNone(enquiry.status_updated_at)
        self.assertLessEqual(enquiry.status_updated_at, timezone.now())

    def test_create_client_group_command_fresh_client_user(self):
        call_command('create_client_group')
        group = Group.objects.get(name='Client')
        self.assertIsNotNone(group)

        fresh_user = User.objects.create_user(
            username='fresh_staff',
            password='Password123!',
            is_staff=True,
        )
        fresh_user.groups.add(group)

        self.client.login(username='fresh_staff', password='Password123!')
        # Cannot access auth user
        resp_forbidden = self.client.get('/panel/auth/user/')
        self.assertIn(resp_forbidden.status_code, [403, 302])

        # Can access quoterequest
        resp_allowed = self.client.get('/panel/core/quoterequest/')
        self.assertEqual(resp_allowed.status_code, 200)

