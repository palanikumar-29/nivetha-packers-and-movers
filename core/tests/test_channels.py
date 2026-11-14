import logging
from unittest.mock import patch, MagicMock
from datetime import date
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from core.models import QuoteRequest, MoveType
from core.channels import dispatch
from core.channels.telegram import send as telegram_send


class ChannelsLayerTest(TestCase):
    def setUp(self):
        self.enquiry = QuoteRequest.objects.create(
            name="Murugan",
            phone="9876543210",
            move_type=MoveType.HOUSE,
            moving_from="Tiruppur",
            moving_to="Tamil Nadu",
            preferred_date=date(2026, 12, 1),
            details="20 boxes and fridge",
            status="New"
        )
        self.secret_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        self.chat_id = "-100123456789"

    @override_settings(TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='')
    def test_dispatch_with_no_channels_configured(self):
        """Verify dispatch runs without error and logs debug message when channels are unconfigured."""
        with self.assertLogs('core.channels', level='DEBUG') as cm:
            dispatch(self.enquiry)
            self.assertTrue(any("No notification channels configured" in msg for msg in cm.output))
            self.assertTrue(any(f"id={self.enquiry.id}" in msg for msg in cm.output))

    @override_settings(TELEGRAM_BOT_TOKEN='dummy_token', TELEGRAM_CHAT_ID='dummy_chat')
    @patch('core.channels.telegram.requests.post')
    def test_dispatch_with_telegram_configured_sends_expected_payload(self, mock_post):
        """Verify requests.post is invoked with chat_id and structured message payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        dispatch(self.enquiry)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("https://api.telegram.org/botdummy_token/sendMessage", args[0])
        self.assertEqual(kwargs['timeout'], 5)
        self.assertEqual(kwargs['json']['chat_id'], 'dummy_chat')
        message_text = kwargs['json']['text']
        self.assertIn("Murugan", message_text)
        self.assertIn("9876543210", message_text)
        self.assertIn("House Move", message_text)
        self.assertIn("Tiruppur", message_text)
        self.assertIn("Tamil Nadu", message_text)
        self.assertIn("2026-12-01", message_text)
        self.assertIn("20 boxes and fridge", message_text)

    @override_settings(TELEGRAM_BOT_TOKEN='test_token_xyz', TELEGRAM_CHAT_ID='chat_999')
    @patch('core.channels.telegram.requests.post', side_effect=Exception("Connection timed out"))
    def test_dispatch_with_telegram_connection_error_caught_and_swallowed(self, mock_post):
        """Verify network connection errors are swallowed and do not propagate to the caller."""
        with self.assertLogs('core.channels', level='ERROR') as cm:
            # Should not raise exception
            dispatch(self.enquiry)
            self.assertTrue(any(f"id={self.enquiry.id}" in msg for msg in cm.output))
            self.assertTrue(any("telegram" in msg.lower() for msg in cm.output))

    @override_settings(TELEGRAM_BOT_TOKEN='secret_token_123', TELEGRAM_CHAT_ID='chat_999')
    @patch('core.channels.telegram.requests.post', side_effect=Exception("Connection refused to api.telegram.org"))
    def test_log_output_never_contains_bot_token_or_telegram_url(self, mock_post):
        """Verify logs never leak the secret bot token or full Telegram endpoint URL."""
        secret_token = "secret_token_123"
        with self.assertLogs('core.channels', level='ERROR') as cm:
            dispatch(self.enquiry)
            combined_logs = "\n".join(cm.output)
            self.assertNotIn(secret_token, combined_logs)
            self.assertNotIn("api.telegram.org", combined_logs)
            self.assertNotIn("Murugan", combined_logs)
            self.assertNotIn("9876543210", combined_logs)

    def test_dispatch_handles_arbitrary_channel_exception(self):
        """Verify any unexpected channel exception is caught, logged, and never propagates."""
        def faulty_channel(enquiry):
            raise RuntimeError("Database connection suddenly dropped")

        with patch('core.channels._get_channels', return_value=[faulty_channel]):
            with self.assertLogs('core.channels', level='ERROR') as cm:
                dispatch(self.enquiry)
                self.assertTrue(any("faulty_channel" in msg for msg in cm.output))
                self.assertTrue(any("RuntimeError" in msg for msg in cm.output))

    @override_settings(TELEGRAM_BOT_TOKEN='tok', TELEGRAM_CHAT_ID='chat')
    @patch('core.channels.telegram.requests.post', side_effect=Exception("Fatal network failure"))
    def test_failing_channel_never_breaks_form_submission_in_view(self, mock_post):
        """Verify visitor form submission on /contact/ still succeeds when notification channel fails."""
        client = Client()
        payload = {
            'name': 'Ganesh',
            'phone': '9876543210',
            'move_type': 'house',
            'moving_from': 'Tiruppur',
            'moving_to': 'Tamil Nadu',
        }
        res = client.post(reverse('core:contact'), data=payload)
        self.assertEqual(res.status_code, 302)
        self.assertIn("?submitted=1#quote-form", res.url)

        follow_res = client.get(res.url)
        self.assertEqual(follow_res.status_code, 200)
        self.assertIn("Thank you! Your quote request has been sent.", follow_res.content.decode('utf-8'))

