from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from core.forms import QuoteForm
from core.models import MoveType, QuoteRequest


class QuoteFormTest(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.future_date = self.today + timedelta(days=7)
        self.past_date = self.today - timedelta(days=1)

    def test_valid_quote_form_with_all_fields(self):
        """Verify form is valid when all required and optional fields are properly formatted."""
        form_data = {
            'name': 'Ramesh Kumar',
            'phone': '9876543210',
            'move_type': MoveType.HOUSE,
            'moving_from': 'Tiruppur',
            'moving_to': 'Chennai',
            'preferred_date': self.future_date.isoformat(),
            'details': '2 BHK flat, ground floor to 2nd floor with lift',
            'website': '',
        }
        form = QuoteForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_valid_quote_form_with_minimal_required_fields(self):
        """Verify form is valid when only required fields are provided."""
        form_data = {
            'name': 'Suresh',
            'phone': '6381234567',
            'move_type': MoveType.VEHICLE,
            'moving_from': 'Tiruppur',
            'moving_to': 'Madurai',
        }
        form = QuoteForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_missing_required_fields_each_cause_validation_error(self):
        """Verify missing name, phone, move_type, moving_from, or moving_to is invalid."""
        required_fields = ['name', 'phone', 'move_type', 'moving_from', 'moving_to']
        for field in required_fields:
            with self.subTest(missing_field=field):
                data = {
                    'name': 'Priya',
                    'phone': '9876543210',
                    'move_type': 'house',
                    'moving_from': 'Tiruppur',
                    'moving_to': 'Madurai',
                }
                data.pop(field)
                form = QuoteForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_phone_number_validation_formats(self):
        """Verify Indian mobile phone number requirements (10 digits starting with 6-9)."""
        valid_phones = ['6381234567', '7901234567', '8123456789', '9876543210']
        for phone in valid_phones:
            with self.subTest(phone=phone):
                form = QuoteForm(data={
                    'name': 'Anand',
                    'phone': phone,
                    'move_type': 'office',
                    'moving_from': 'Tiruppur',
                    'moving_to': 'Chennai',
                })
                self.assertTrue(form.is_valid(), f"Expected {phone} to be valid: {form.errors}")

        invalid_phones = [
            '1234567890',    # Starts with 1
            '5876543210',    # Starts with 5
            '987654321',     # 9 digits
            '98765432100',   # 11 digits
            '98765abcde',    # Contains letters
            '+919876543210', # Contains +91
            '9876 543210',   # Whitespace inside
        ]
        for phone in invalid_phones:
            with self.subTest(invalid_phone=phone):
                form = QuoteForm(data={
                    'name': 'Anand',
                    'phone': phone,
                    'move_type': 'office',
                    'moving_from': 'Tiruppur',
                    'moving_to': 'Chennai',
                })
                self.assertFalse(form.is_valid())
                self.assertIn('phone', form.errors)

    def test_preferred_date_today_and_future_are_valid(self):
        """Verify today's date and future dates are accepted as preferred move date."""
        for test_date in [self.today, self.future_date]:
            with self.subTest(date=test_date):
                form = QuoteForm(data={
                    'name': 'Kavitha',
                    'phone': '9876543210',
                    'move_type': 'house',
                    'moving_from': 'Tiruppur',
                    'moving_to': 'Chennai',
                    'preferred_date': test_date.isoformat(),
                })
                self.assertTrue(form.is_valid(), f"Date {test_date} should be valid: {form.errors}")

    def test_preferred_date_in_past_is_rejected(self):
        """Verify preferred date in the past raises validation error."""
        form = QuoteForm(data={
            'name': 'Kavitha',
            'phone': '9876543210',
            'move_type': 'house',
            'moving_from': 'Tiruppur',
            'moving_to': 'Chennai',
            'preferred_date': self.past_date.isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('preferred_date', form.errors)
        self.assertIn("Preferred move date must be today or a future date.", form.errors['preferred_date'])

    def test_honeypot_website_field_is_recognized(self):
        """Verify the honeypot website field is accepted by form for server inspection."""
        form = QuoteForm(data={
            'name': 'SpamBot',
            'phone': '9876543210',
            'move_type': 'house',
            'moving_from': 'Tiruppur',
            'moving_to': 'Chennai',
            'website': 'https://spam-link.xyz',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['website'], 'https://spam-link.xyz')
