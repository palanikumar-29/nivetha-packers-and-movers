from datetime import timedelta
from django.test import TestCase
from django.db import connection
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import QuoteRequest, Service, GalleryImage, MoveType, EnquiryStatus


class ModelTablesTest(TestCase):
    def test_tables_created_after_migration(self):
        """Verify all three model tables exist in the database."""
        table_names = connection.introspection.table_names()
        self.assertIn('core_quoterequest', table_names)
        self.assertIn('core_service', table_names)
        self.assertIn('core_galleryimage', table_names)


class ServiceModelTest(TestCase):
    def test_create_and_read_service(self):
        """Verify creating a Service record and reading it back."""
        service = Service.objects.create(
            title='House Shifting',
            description='Safe and secure domestic relocation within and across cities.',
            order=1,
            is_active=True
        )
        saved = Service.objects.get(pk=service.pk)
        self.assertEqual(saved.title, 'House Shifting')
        self.assertEqual(saved.description, 'Safe and secure domestic relocation within and across cities.')
        self.assertEqual(saved.order, 1)
        self.assertTrue(saved.is_active)
        self.assertEqual(str(saved), 'House Shifting')

    def test_service_ordering(self):
        """Verify services order by 'order', then 'id'."""
        s2 = Service.objects.create(title='Vehicle Transport', order=2)
        s1 = Service.objects.create(title='Office Moving', order=1)
        services = list(Service.objects.all())
        self.assertEqual(services[0], s1)
        self.assertEqual(services[1], s2)


class QuoteRequestModelTest(TestCase):
    def test_create_and_read_quote_request(self):
        """Verify creating a QuoteRequest record with status=New and reading it back."""
        future_date = timezone.localdate() + timedelta(days=7)
        quote = QuoteRequest.objects.create(
            name='Kavitha',
            phone='9876543210',
            move_type=MoveType.HOUSE,
            moving_from='Tiruppur',
            moving_to='Tamil Nadu',
            preferred_date=future_date,
            details='2 BHK household items',
            status=EnquiryStatus.NEW,
            notes='Initial enquiry'
        )
        saved = QuoteRequest.objects.get(pk=quote.pk)
        self.assertEqual(saved.name, 'Kavitha')
        self.assertEqual(saved.phone, '9876543210')
        self.assertEqual(saved.move_type, MoveType.HOUSE)
        self.assertEqual(saved.moving_from, 'Tiruppur')
        self.assertEqual(saved.moving_to, 'Tamil Nadu')
        self.assertEqual(saved.preferred_date, future_date)
        self.assertEqual(saved.status, EnquiryStatus.NEW)
        self.assertEqual(str(saved), 'Kavitha — House Move (New)')

    def test_phone_number_validation_success(self):
        """Verify valid 10-digit Indian mobile numbers pass validation."""
        valid_phones = ['6123456789', '7987654321', '8012345678', '9988776655']
        for phone in valid_phones:
            quote = QuoteRequest(
                name='Ramesh',
                phone=phone,
                moving_from='Tiruppur',
                moving_to='Tamil Nadu'
            )
            try:
                quote.full_clean()
            except ValidationError:
                self.fail(f"Phone {phone} should be valid but raised ValidationError")

    def test_phone_number_validation_rejection(self):
        """Verify invalid phones are rejected."""
        invalid_phones = [
            '1234567890',  # starts with 1
            '5123456789',  # starts with 5
            '98765',       # too short
            '98765432100', # too long
            '98765abcde',  # alphabetic
            '',            # blank
        ]
        for phone in invalid_phones:
            quote = QuoteRequest(
                name='Ramesh',
                phone=phone,
                moving_from='Tiruppur',
                moving_to='Tamil Nadu'
            )
            with self.assertRaises(ValidationError):
                quote.full_clean()

    def test_enquiry_with_past_preferred_date_can_be_saved_and_status_updated(self):
        """
        Verify that an existing enquiry with a past preferred_date does NOT fail
        model validation, allowing status changes and internal notes updates.
        (Future-date validation applies only to the public submission form in Story 1.4).
        """
        past_date = timezone.localdate() - timedelta(days=14)
        quote = QuoteRequest.objects.create(
            name='Suresh',
            phone='9876543210',
            moving_from='Tiruppur',
            moving_to='Salem',
            preferred_date=past_date,
            status=EnquiryStatus.NEW
        )

        # full_clean() should pass without ValidationError
        quote.full_clean()

        # Update status and internal notes
        quote.status = EnquiryStatus.CALLED
        quote.notes = 'Customer called on Nov 3; confirmed packing scheduled.'
        quote.save()

        refreshed = QuoteRequest.objects.get(pk=quote.pk)
        self.assertEqual(refreshed.status, EnquiryStatus.CALLED)
        self.assertEqual(refreshed.notes, 'Customer called on Nov 3; confirmed packing scheduled.')
        self.assertEqual(refreshed.preferred_date, past_date)
        self.assertIsNotNone(refreshed.status_updated_at)

    def test_enquiry_with_past_date_can_be_saved_through_admin_form(self):
        """
        Verify that in the admin panel (/panel/), an enquiry with a past preferred_date
        can be edited and saved via the admin form without validation errors.
        """
        from django.contrib.admin.sites import AdminSite
        from core.admin import QuoteRequestAdmin

        past_date = timezone.localdate() - timedelta(days=30)
        quote = QuoteRequest.objects.create(
            name='Dhanasekar',
            phone='9876543210',
            moving_from='Tiruppur',
            moving_to='Tamil Nadu',
            preferred_date=past_date,
            status=EnquiryStatus.NEW
        )

        site = AdminSite()
        admin_instance = QuoteRequestAdmin(QuoteRequest, site)
        FormClass = admin_instance.get_form(None, obj=quote)

        # Simulate editing status and notes in the admin panel
        form_data = {
            'name': quote.name,
            'phone': quote.phone,
            'move_type': quote.move_type,
            'moving_from': quote.moving_from,
            'moving_to': quote.moving_to,
            'preferred_date': quote.preferred_date,
            'details': quote.details,
            'status': EnquiryStatus.CONFIRMED,
            'notes': 'Move completed successfully; marked confirmed by admin.',
        }
        form = FormClass(data=form_data, instance=quote)
        self.assertTrue(form.is_valid(), f"Admin form errors: {form.errors}")
        saved_instance = form.save()
        self.assertEqual(saved_instance.status, EnquiryStatus.CONFIRMED)
        self.assertEqual(saved_instance.preferred_date, past_date)

    def test_status_update_timestamp(self):
        """Verify changing status sets status_updated_at."""
        quote = QuoteRequest.objects.create(
            name='Naveen',
            phone='9876543210',
            moving_from='Tiruppur',
            moving_to='Coimbatore',
            status=EnquiryStatus.NEW
        )
        self.assertIsNone(quote.status_updated_at)

        quote.status = EnquiryStatus.CALLED
        quote.save()

        refreshed = QuoteRequest.objects.get(pk=quote.pk)
        self.assertEqual(refreshed.status, EnquiryStatus.CALLED)
        self.assertIsNotNone(refreshed.status_updated_at)


class GalleryImageModelTest(TestCase):
    def test_create_and_read_gallery_image(self):
        """Verify GalleryImage model creation and default local storage."""
        dummy_image = SimpleUploadedFile(
            name='test_truck.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/gif'
        )
        gallery_img = GalleryImage.objects.create(
            image=dummy_image,
            caption='Packing household goods securely in Tiruppur',
            order=1,
            is_active=True
        )
        saved = GalleryImage.objects.get(pk=gallery_img.pk)
        self.assertEqual(saved.caption, 'Packing household goods securely in Tiruppur')
        self.assertTrue(saved.is_active)
        self.assertEqual(saved.order, 1)
        self.assertEqual(str(saved), 'Packing household goods securely in Tiruppur')
        self.assertTrue(saved.image.name.startswith('gallery/'))

