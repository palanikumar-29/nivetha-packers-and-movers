from django.shortcuts import render
from .models import Service, GalleryImage


def home(request):
    """
    Home page view displaying hero, road-sign route board, services summary,
    how a move works steps, and the quote request form markup.
    """
    services = Service.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'home.html', {
        'services': services,
    })


def services(request):
    """
    Services page view displaying all active services in order as a ruled list,
    with an empty state fallback and quote CTA.
    """
    services_list = Service.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'services.html', {
        'services': services_list,
    })


def gallery(request):
    """
    Gallery page view displaying active gallery images with lazy loading,
    image captions as alt text, and an empty state fallback.
    """
    images = GalleryImage.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'gallery.html', {
        'images': images,
    })


def about(request):
    """
    About page view with neutral, verifiable details about the business.
    """
    return render(request, 'about.html')


def contact(request):
    """
    Contact page view with phone, WhatsApp, address, and quote form markup.
    """
    return render(request, 'contact.html')
