from django.shortcuts import render
from .models import Service


def home(request):
    """
    Home page view displaying hero, road-sign route board, services summary,
    how a move works steps, and the quote request form markup.
    """
    services = Service.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'home.html', {
        'services': services,
    })
