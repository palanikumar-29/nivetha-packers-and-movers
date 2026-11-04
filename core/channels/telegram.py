import logging
import requests
from django.conf import settings
from core.models import QuoteRequest

logger = logging.getLogger(__name__)


def send(enquiry: QuoteRequest) -> None:
    """
    Send notification to configured Telegram chat.
    Does not log the bot token, Telegram URL, or customer PII.
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
    if not bot_token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    preferred_date_str = enquiry.preferred_date.strftime('%Y-%m-%d') if enquiry.preferred_date else 'Not specified'
    details_str = f"\nDetails: {enquiry.details}" if enquiry.details else ""

    text = (
        f"New Quote Request (ID: {enquiry.id})\n"
        f"Name: {enquiry.name}\n"
        f"Phone: {enquiry.phone}\n"
        f"Move Type: {enquiry.get_move_type_display()}\n"
        f"From: {enquiry.moving_from}\n"
        f"To: {enquiry.moving_to}\n"
        f"Preferred Date: {preferred_date_str}"
        f"{details_str}"
    )

    try:
        response = requests.post(
            url,
            json={'chat_id': chat_id, 'text': text},
            timeout=5
        )
        response.raise_for_status()
        logger.info("Channel telegram succeeded for enquiry id=%s", enquiry.id)
    except Exception as exc:
        # Avoid logging the URL as it contains the bot token, and avoid customer PII
        logger.error(
            "Channel telegram failed for enquiry id=%s: %s",
            enquiry.id,
            type(exc).__name__
        )
        raise

