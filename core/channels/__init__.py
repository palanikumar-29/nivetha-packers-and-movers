import logging
from typing import List, Callable
from django.conf import settings
from core.models import QuoteRequest

logger = logging.getLogger(__name__)


def dispatch(enquiry: QuoteRequest) -> None:
    """
    Call all registered notification channels.
    Swallow every exception so that a channel failure never breaks form submission.
    """
    try:
        channels = _get_channels()
        if not channels:
            logger.debug("No notification channels configured for enquiry id=%s", enquiry.id)
            return

        for channel_fn in channels:
            channel_name = getattr(channel_fn, '__name__', str(channel_fn))
            try:
                channel_fn(enquiry)
            except Exception as exc:
                logger.error(
                    "Channel %s failed for enquiry id=%s: %s",
                    channel_name,
                    enquiry.id,
                    type(exc).__name__
                )
    except Exception as exc:
        logger.error(
            "Notification dispatch failed for enquiry id=%s: %s",
            getattr(enquiry, 'id', None),
            type(exc).__name__
        )


def _get_channels() -> List[Callable[[QuoteRequest], None]]:
    """Return list of active channel send functions based on settings."""
    channels = []
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
    if bot_token and chat_id:
        from .telegram import send
        channels.append(send)
    return channels

