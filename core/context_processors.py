from django.conf import settings

def business_contact(request):
    """Provide business contact configuration to templates without hardcoding."""
    return {
        'BUSINESS_PHONE': getattr(settings, 'BUSINESS_PHONE', ''),
        'BUSINESS_WHATSAPP': getattr(settings, 'BUSINESS_WHATSAPP', ''),
    }

