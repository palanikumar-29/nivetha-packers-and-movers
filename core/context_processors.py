import json
from django.conf import settings


def business_contact(request):
    """Provide business contact configuration to templates without hardcoding."""
    return {
        'BUSINESS_PHONE': getattr(settings, 'BUSINESS_PHONE', ''),
        'BUSINESS_WHATSAPP': getattr(settings, 'BUSINESS_WHATSAPP', ''),
        'BUSINESS_ADDRESS': getattr(settings, 'BUSINESS_ADDRESS', 'Tiruppur, Tamil Nadu'),
    }


def seo_context(request):
    """Provide JSON-LD schema and SEO metadata without hardcoding."""
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    phone = getattr(settings, 'BUSINESS_PHONE', '').strip()
    address_val = getattr(settings, 'BUSINESS_ADDRESS', 'Tiruppur, Tamil Nadu').strip()

    schema = {
        "@context": "https://schema.org",
        "@type": "MovingCompany",
        "name": "Nivetha Packers and Movers",
        "url": site_url,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": address_val,
            "addressLocality": "Tiruppur",
            "addressRegion": "Tamil Nadu",
            "addressCountry": "IN",
        },
        "areaServed": [
            "Tiruppur",
            "Chennai",
            "Madurai",
        ],
    }
    if phone:
        schema["telephone"] = phone

    return {
        'SITE_URL': site_url,
        'schema_json': json.dumps(schema),
    }
